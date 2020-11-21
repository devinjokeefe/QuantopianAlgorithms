from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data import morningstar
from quantopian.pipeline.filters.morningstar import Q1500US
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors import CustomFactor

def initialize(context):
    
    # Rebalance monthly on the first day of the week at market open
    schedule_function(rebalance,
                      date_rule=date_rules.every_day(),
                      time_rule=time_rules.market_open())

    attach_pipeline(make_pipeline(context), 'value_investing')
    
class NCAV_Ratio(CustomFactor):
    inputs = [morningstar.balance_sheet.cash_and_cash_equivalents, 
              morningstar.balance_sheet.total_liabilities, 
              morningstar.valuation.market_cap]
    
    window_length = 1
    
    def compute(self, today, assets, out, cash, liabilities, mkt_cap):
        out[:] = (cash[-1] - liabilities[-1]) / mkt_cap[-1]
    
def make_pipeline(context):
    
    NCAV_Rto = NCAV_Ratio() 
    #filters
    Low_NCAV = NCAV_Rto >= 2
    is_profitable = morningstar.income_statement.gross_profit >= 0
    
    universe = Q1500US() & Low_NCAV & is_profitable 
    
    securities_to_trade = (universe)
    
    pipe = Pipeline(
              columns={
                'NCAV': NCAV_Rto,
                'profit': morningstar.income_statement.gross_profit.latest,
                'longs': universe,
              },
              screen = securities_to_trade
          )

    return pipe

def before_trading_start(context, data): 

    context.pipe_output = pipeline_output('value_investing')

    context.longs = context.pipe_output[context.pipe_output['longs']].index
    
def rebalance(context, data):
    
    my_positions = context.portfolio.positions
    long_weight = 0.033
    
    if(len(context.longs > 0)):
        target_long_symbols = [s.symbol for s in context.longs]
        print target_long_symbols
        
        for security in context.longs:
            if data.can_trade(security):
                if security not in my_positions:
                    order_target_percent(security, long_weight)
            else:
                log.info("Didn't open long position in %s" % security)
    
    closed_positions = []
    
    # Close our previous positions that are no longer in our pipeline.
    for security in my_positions:
        if security not in context.longs and security not in context.shorts \
        and data.can_trade(security):
            order_target_percent(security, 0)
            closed_positions.append(security)
    
    log.info("Closing our positions in %s." % ','.join([s.symbol for s in closed_positions]))