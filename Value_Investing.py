#from quantopian.algorithm import attach_pipeline, pipeline_output
#from quantopian.pipeline import Pipeline
#from quantopian.pipeline.data import morningstar
#from quantopian.pipeline.filters.morningstar import Q1500US
#from quantopian.pipeline import CustomFactor

#def initialize (context): 
    
#class NCAV_Ratio (CustomFactor):
#   inputs = [morningstar.balance_sheet.cash_and_cash_equivalents,
#             morningstar.balance_sheet.total_liabilities,
#             morningstar.valuation.market_cap]
    
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline import CustomFactor
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.data import morningstar
from quantopian.pipeline.filters.morningstar import Q1500US
from quantopian.pipeline.factors import AverageDollarVolume

class NetCash(CustomFactor):
    inputs = [morningstar.balance_sheet.cash_and_cash_equivalents,
             morningstar.balance_sheet.total_liabilities,
             morningstar.valuation.market_cap]
    window_length = 1
    
    def compute(self, today, assets, out, cash, liab, markCap):
        out[:] = (cash[0] - liab[0]) / markCap[0]

#class Profit(CustomFactor):
#    inputs = [morningstar.cash_flow_statement

def initialize(context):
    EntVal = NetCash()
    
    schedule_function(rebalance,
                      date_rules.week_start(),
                      time_rules.market_open())

    # Create and apply a filter representing the top 500 equities by MarketCap
    # every day.
    # Construct an average dollar volume factor

    NegEnt = EntVal > 1
    
    LongsUniverse = Q1500US()#& NegEnt
    longs = EntVal.top(25, mask=LongsUniverse)

    hold = Q1500US() & NegEnt
    
    pipe = Pipeline(screen = longs, columns = {'Longs':longs})
    attach_pipeline(pipe, 'Value_Investing')

    pipe2 = Pipeline(screen = hold, columns = None)
    attach_pipeline(pipe2, 'Hold')
    
def before_trading_start(context, data):
    context.output = pipeline_output('Value_Investing')
    context.security_list = context.output.index
    
    context.holdOutput = pipeline_output('Hold')
    context.hold_list = context.holdOutput.index
    
def rebalance(context, data):
    """
    This function is called according to our schedule_function settings and calls
    order_target_percent() on every security in weights.
    """
    trailing_stop_loss (context, data)
        
def trailing_stop_loss (context, data):
    
    cash_on_hand = context.portfolio.cash
    
    if cash_on_hand < 0:
        cash_on_hand = 5000
    
    num = cash_on_hand / len(context.security_list)
    print (num)
    for sec in context.portfolio.positions:
        if sec not in context.hold_list:
            order_target_value(sec, 0.0)
            print ("Selling: " + str(sec))
    
    for security in context.security_list:
        order_target_value(security, num)