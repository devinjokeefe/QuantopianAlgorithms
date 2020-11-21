from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors import AverageDollarVolume
from quantopian.pipeline.filters import Q1500US 
from quantopian.pipeline import CustomFactor
from quantopian.pipeline.data import morningstar
from quantopian.pipeline.data import Fundamentals

def initialize(context):
    # Rebalance every day, 1 hour after market open.
    schedule_function(my_rebalance, date_rules.week_start(), time_rules.market_open(hours=3))
     
    # Create our dynamic stock selector.
    attach_pipeline(make_pipeline(), 'pipe')
    
class EV(CustomFactor):
    # Pre-declare inputs and window_length
    inputs = [Fundamentals.cash_and_cash_equivalents,
             Fundamentals.total_liabilities,
             Fundamentals.market_cap]
    window_length = 1

    def compute(self, today, assets, out, c, l, m):
        out[:] = c[-1] - l[-1] - m[-1]

   
class EBITDA(CustomFactor):
    inputs = [Fundamentals.ebitda,
             Fundamentals.market_cap]
    window_length = 1
    
    def compute(self, today, assets, out, EBITDA, mc):
        out[:] = EBITDA[-1] / mc[-1]

def make_pipeline():
    
    ev = EV()
    excessCash = Fundamentals.enterprise_value.latest < 0
    
    Earnings = EBITDA()
    isProfitable = Fundamentals.ebitda.latest > 0 
    
    notFinance = Fundamentals.morningstar_sector_code != 103
    
    universe = Q1500US() & excessCash & notFinance
    buys = ev.top(5, mask=universe)
    
    longsUniverse = ev.top(5, mask=universe)
    
    tempEVMC = Fundamentals.enterprise_value.latest / Fundamentals.market_cap.latest
    evmc = tempEVMC < 0.7
    
    pipe = Pipeline(
        screen = longsUniverse,
        columns = {
            'Buys': buys,
            'EVMC': evmc
        }
    )
    
    return pipe
 
def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    context.output = pipeline_output('pipe')
    context.evmc = context.output[context.output['EVMC']].index
    context.buys = context.output[context.output['Buys']].index  

    # These are the securities that we are interested in trading each day.
    context.security_list = context.output.index
    
def my_rebalance(context, data):
    invest = 0.0
    
    if (len(context.security_list > 0)):
        invest = 1.0 / len(context.security_list)
        print (invest)
    
    if (invest > 0.2):
        invest = 0.2
    try:
        print ("Percentage of cash not deployed: {}".format(context.portfolio.cash // context.portfolio.capital_used))
    except:
        print ("Capital not deployed")
    
    for security in context.buys:
            print ("Buying ", invest, " worth of ", security)
            order_target_percent(security, invest)
            
    positions = context.portfolio.positions
        
    for security, value in positions.items():
        if (security not in context.evmc):
            print ("Selling this security : {}".format(security))
            
            order_target_value(security, 0)