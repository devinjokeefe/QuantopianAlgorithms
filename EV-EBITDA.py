"""
This is a template algorithm on Quantopian for you to adapt and fill in.
"""
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
    inputs = [morningstar.valuation.enterprise_value]
    window_length = 1

    # Compute market cap value
    def compute(self, today, assets, out, EV):
        out[:] = -1 * EV[-1]
        
class marketCap(CustomFactor):
    # Pre-declare inputs and window_length
    inputs = [morningstar.valuation.market_cap]
    window_length = 1

    # Compute market cap value
    def compute(self, today, assets, out, MC):
        out[:] = -1 * MC[-1]
   
class PosEBITDA(CustomFactor):
    inputs = [morningstar.income_statement.ebitda]
    window_length = 1
    
    def compute(self, today, assets, out, EBITDA):
        out[:] = EBITDA[-1]

def make_pipeline():
    
    ev = EV()
    excessCash = ev > 0
    
    EBITDA = PosEBITDA()
    isProfitable = EBITDA > 0 
    
    universe = Q1500US() & excessCash & isProfitable
    longsUniverse = ev.top(10, mask=universe)
    
    pipe = Pipeline(
        screen = longsUniverse,
        #columns = {
        #    'close': yesterday_close,
        #}
    )
    return pipe
 
def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    context.output = pipeline_output('pipe')
  
    # These are the securities that we are interested in trading each day.
    context.security_list = context.output.index
    
def my_rebalance(context, data):
    
    invest = context.account.available_funds / len(context.security_list)
    
    for security in context.security_list:
        ev = EV()
        evS = ev[security]
        
        mc = marketCap()
        mcS = mc[security]
        if (evS > 0):
            print ("The EV% of this security is : {}".format(evS))
            order_target_value(security, 0)
            
        else:
            order_value(security, invest)
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
        