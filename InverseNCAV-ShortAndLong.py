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

# Create custom factor subclass to calculate a market cap based on yesterday's
# close
class NCAVRatio(CustomFactor):
    # Pre-declare inputs and window_length
    inputs = [morningstar.balance_sheet.cash_and_cash_equivalents,
             morningstar.balance_sheet.accounts_receivable,
             morningstar.balance_sheet.inventory,
             morningstar.balance_sheet.total_liabilities,
             morningstar.valuation.market_cap]
    window_length = 1

    # Compute market cap value
    def compute(self, today, assets, out, cash, accounts, inventory, liabilities, cap):
        out[:] = ((cash[-1] + 0.75 * accounts[-1] + 0.5 * inventory [-1])- liabilities[-1]) / cap[-1]
        
class InverseNCAV(CustomFactor):
    # Pre-declare inputs and window_length
    inputs = [morningstar.balance_sheet.cash_and_cash_equivalents,
             morningstar.balance_sheet.accounts_receivable,
             morningstar.balance_sheet.inventory,
             morningstar.balance_sheet.total_liabilities,
             morningstar.valuation.market_cap]
    window_length = 1

    # Compute market cap value
    def compute(self, today, assets, out, cash, accounts, inventory, liabilities, cap):
        out[:] =  cap[-1] / ((cash[-1] + 0.75 * accounts[-1] + 0.5 * inventory [-1])- liabilities[-1])        

class PE(CustomFactor):
    inputs = [morningstar.income_statement.net_income,
             morningstar.valuation.shares_outstanding,
             USEquityPricing.close]
    window_length = 1
    
    def compute(self, today, assets, out, net, shares, price):
        out[:] = price / (net[-1] / shares[-1])
        
class Dividends(CustomFactor):
    inputs = [morningstar.valuation_ratios.dividend_yield]
    window_length = 252
    
    def compute(self, today, assets, out, dividends):
        out[:] = dividends[-1]
        
def initialize(context):
    NCAV = NCAVRatio()
    NCAVINV = InverseNCAV()
    
    schedule_function(rebalance,
                      date_rules.week_start(),
                      time_rules.market_open())

    # Create and apply a filter representing the top 500 equities by MarketCap
    # every day.
    # Construct an average dollar volume factor

    PERatio = PE()
    Solid_PE = PERatio < 10
    Short_PE = PERatio > 50
    
    div = Dividends()
    Solid_Div = div >= 0.02
    Short_Div = PERatio >100
    
    LongsUniverse = Q1500US() & Solid_PE & Solid_Div#& Not_Bio#& high_dollar_volume 
    ShortsUniverse = Q1500US() & Short_PE & Short_Div
    # Create filters for our long and short portfolios.
    longs = NCAV.top(15, mask=LongsUniverse)
    shortsTest = NCAVINV.top(15)
    shorts = NCAVINV.top(15, mask=ShortsUniverse)
    print "List of stocksTEST for short position : {}".format(shortsTest)
    print "List of stocks for short position : {}".format(shorts)
    Universe= (longs|shorts|shortsTest)

    pipe = Pipeline(columns = {'longs': longs, 'shorts': shorts, 'shortsTest': shortsTest}, screen = Universe)
    attach_pipeline(pipe, 'Value_Investing')

def before_trading_start(context, data):
    context.output = pipeline_output('Value_Investing')
    context.longs = context.output[context.output['longs']].index.tolist()
    context.shorts = context.output[context.output['shorts']].index.tolist()
    context.shortsTest = context.output[context.output['shortsTest']].index.tolist()
    print "List of stocks for short position : {}".format(context.shorts)
    print "List of stocks for shortTEST position : {}".format(context.shortsTest)
    
def rebalance(context, data):
    """
    This function is called according to our schedule_function settings and calls
    order_target_percent() on every security in weights.
    """
    trailing_stop_loss (context, data)
        
def trailing_stop_loss (context, data):
    
    PERatio = PE()
    NCAV = NCAVRatio()
    High_PE = 0
    High_NCAV = 0
    
    for security in context.shorts:
        
        if PERatio < 30:
            order_target_percent(security, 0)
            High_PE += 1
            print "{} times stock sold for too low PE Ratio".format(High_PE)
            context.short_list.remove(security)
        
        elif NCAV < 15:
            order_target_percent(security, 0)
            High_NCAV += 1
            print "{} times stock sold for too low NCAV Ratio".format(High_NCAV)
            context.short_list.remove(security)
    
    for security in context.longs:
        
        price_history = data.history(
        security,
        fields='price',
        bar_count=120,
        frequency='1d'
        )
        
        high_price = max(price_history)
        tsl = high_price * 0.92
        current_price = data.current(security, 'price')
        
        if current_price < tsl:
            order_target_percent(security, 0)
            print "selling {} as it has crossed the trailing stop loss".format(security)
            context.longs.remove(security)
            order_target_value(security, 0)
            
        elif PERatio > 20:
            order_target_percent(security, 0)
            High_PE += 1
            print "{} times stock sold for too high PE Ratio".format(High_PE)
            context.longs.remove(security)
            order_target_value(security, 0)
            
        elif NCAV > 3:
            order_target_percent(security, 0)
            High_NCAV += 1
            print "{} times stock sold for too high NCAV Ratio".format(High_NCAV)
            context.longs.remove(security)
            order_target_value(security, 0)
            
    length = len(context.longs) + len(context.shorts)
    num = context.portfolio.cash / length
    
    for security in context.longs:
        order_target_value(security, num)
        
    for security in context.shorts:
		print "Buying {} in short position".format(security)
		order_target_value(security, -num)