import numpy as np
import pandas as pd
import datetime
#template is Naoki Nagai's growth stock picking algo

def initialize(context):
    # Dictionary of stocks and their respective weights
    context.stock_weights = {}
    
    # Rebalance monthly on the first day of the month at market open
    schedule_function(rebalance,                      
                      date_rule=date_rules.month_start(),
                      time_rule=time_rules.market_open())
    
def rebalance(context, data):
    # Track cash to avoid leverage
    cash = context.portfolio.cash
    
    # Exit all positions before starting new ones
    for stock in context.portfolio.positions:
        if stock not in context.fundamental_df:
            order_target(stock, 0)
            cash += context.portfolio.positions[stock].amount
            
    # Create weights for each stock
    weight = create_weights(context, context.stocks)

    # Rebalance all stocks to target weights
    for stock in context.fundamental_df:
        if weight != 0 and stock in data and data.can_trade(stock):
            notional = context.portfolio.portfolio_value * weight
            price = data[stock].price
            if np.isfinite(price) != True:  
                    price = 1
                    notional = 0
            numshares = int(notional / price)
            
       #Removed the thin trading screen here
       #buy the stock
        if cash > price * numshares: 
            order_target_percent(stock, weight)
            cash -= notional - context.portfolio.positions[stock].amount  
    
def before_trading_start(context): 
    """
      Called before the start of each trading day. 
      It updates our universe with the
      securities and values found from fetch_fundamentals.
    """

    #Changed from 100 in the original template to 30 here
    num_stocks = 30
    
    # Setup SQLAlchemy query to screen stocks based on PE ration
    # and industry sector. Then filter results based on 
    # market cap and shares outstanding.
    # We limit the number of results to num_stocks and return the data
    # in descending order.
    fundamental_df = get_fundamentals(
        query(
            # put your query in here by typing "fundamentals."
            fundamentals.valuation.market_cap,
            fundamentals.valuation.shares_outstanding,
            fundamentals.income_statement.total_revenue,
            fundamentals.valuation.enterprise_value,
            fundamentals.company_reference.country_id,
            fundamentals.asset_classification.morningstar_sector_code
        )
        
        #penny stocks       
        .filter(fundamentals.valuation.market_cap < 5e7)
        .filter(fundamentals.valuation.enterprise_value < 0)
        
        .filter(fundamentals.company_reference.country_id.in_(['USA']))
        #shares tradable sanity check stays in
        .filter(fundamentals.valuation.shares_outstanding != None)
        
        .order_by(fundamentals.valuation.shares_outstanding.desc())
        .limit(num_stocks)
    )

    # Filter out only stocks that fit in criteria
    context.stocks = [stock for stock in fundamental_df]
    
    # Update context.fundamental_df with the securities that we need
    context.fundamental_df = fundamental_df[context.stocks]
    
    update_universe(context.fundamental_df.columns.values)   
    
    record (cash = context.portfolio.cash, asset = context.portfolio.portfolio_value)
    
def create_weights(context, stocks):
    """
        Takes in a list of securities and weights them all equally 
    """
    if len(stocks) == 0:
        return 0 
    else:
        # Buy 0.95 of portfolio value to avoid borrowing, increased from 0.90
        weight = .95/len(stocks)
        return weight
        
def handle_data(context, data):
    """
      Code logic to run during the trading day.
      handle_data() gets called every bar.
    """
    pass