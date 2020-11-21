from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors import AverageDollarVolume
from quantopian.pipeline.filters import Q1500US 
from quantopian.pipeline import CustomFactor
from quantopian.pipeline.data import morningstar

def initialize(context):
    # Rebalance every day, 1 hour after market open.
    schedule_function(my_rebalance, date_rules.week_start(), time_rules.market_open(hours=3))
     
    # Create our dynamic stock selector.
    attach_pipeline(make_pipeline(), 'pipe')
    
class EV(CustomFactor):
    # Pre-declare inputs and window_length
    inputs = [morningstar.balance_sheet.cash_cash_equivalents_and_marketable_securities,
             morningstar.balance_sheet.current_liabilities,
             morningstar.valuation.market_cap]
    window_length = 1

    def compute(self, today, assets, out, cash, liabilities, marketCap):
        out[:] = cash[-1] - liabilities[-1] - marketCap[-1]

   
class EBITDA(CustomFactor):
    inputs = [morningstar.income_statement.ebitda,
             morningstar.valuation.market_cap]
    window_length = 1
    
    def compute(self, today, assets, out, EBITDA, mc):
        out[:] = EBITDA[-1] / mc[-1]

def make_pipeline():
    
    ev = EV()
    excessCash = morningstar.valuation.enterprise_value.latest < 0
    
    Earnings = EBITDA()
    isProfitable = morningstar.income_statement.ebitda.latest > 0 
    
    universe = Q1500US() & excessCash & isProfitable
    longsUniverse = ev.top(25, mask=universe)
    
    tempEVMC = morningstar.valuation.enterprise_value.latest / morningstar.valuation.market_cap.latest
    evmc = tempEVMC < 0.5
    
    pipe = Pipeline(
        screen = longsUniverse,
        columns = {
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
  
    # These are the securities that we are interested in trading each day.
    context.security_list = context.output.index
    
def my_rebalance(context, data):
    
    #print ("number of holds {}".format(len(context.holds)))
    
    if (len(context.security_list) > 0):
        invest = context.account.available_funds / len(context.security_list)

    for security in context.security_list:
            print ("Buying ", invest, " worth of ", security)
            order_value(security, invest)
            
    positions = context.portfolio.positions
        
    for security, value in positions.items():
        if (security not in context.evmc):
            print ("Selling this security : {}".format(security))
            
            order_target_value(security, 0)
            
            
            
            
            
            
            
            
            
            
            