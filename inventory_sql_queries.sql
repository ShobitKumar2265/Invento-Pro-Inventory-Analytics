-- ================================================================
-- INVENTORY OPTIMIZATION PROJECT — SQL QUERY LIBRARY
-- Domain: Retail / Supply Chain Analytics
-- Period: July – December 2024 | 75 Products | 5 Categories
-- ================================================================

-- ================================================================
-- SECTION 1: DATABASE SETUP & TABLE CREATION
-- ================================================================

-- Create Products Master Table
CREATE TABLE IF NOT EXISTS products (
    product_id      VARCHAR(10)     PRIMARY KEY,
    product_name    VARCHAR(100)    NOT NULL,
    category        VARCHAR(50)     NOT NULL,
    unit_cost       DECIMAL(10,2)   NOT NULL,
    selling_price   DECIMAL(10,2)   NOT NULL,
    reorder_point   INT             NOT NULL,
    lead_time_days  INT             NOT NULL,
    safety_stock    INT             NOT NULL,
    max_stock_level INT             NOT NULL,
    supplier        VARCHAR(50)
);

-- Create Sales Transactions Table
CREATE TABLE IF NOT EXISTS sales (
    sale_id         VARCHAR(15)     PRIMARY KEY,
    product_id      VARCHAR(10)     REFERENCES products(product_id),
    product_name    VARCHAR(100),
    category        VARCHAR(50),
    sale_date       DATE            NOT NULL,
    units_sold      INT             NOT NULL,
    unit_price      DECIMAL(10,2)   NOT NULL,
    revenue         DECIMAL(12,2)   NOT NULL,
    cogs            DECIMAL(12,2)   NOT NULL
);

-- Create Inventory Movements Table
CREATE TABLE IF NOT EXISTS inventory (
    record_id       SERIAL          PRIMARY KEY,
    record_date     DATE            NOT NULL,
    product_id      VARCHAR(10)     REFERENCES products(product_id),
    opening_stock   INT             NOT NULL,
    units_received  INT             DEFAULT 0,
    units_sold      INT             DEFAULT 0,
    closing_stock   INT             NOT NULL,
    reorder_point   INT,
    stockout_flag   SMALLINT        DEFAULT 0,  -- 1 = stockout occurred
    overstock_flag  SMALLINT        DEFAULT 0   -- 1 = overstock condition
);

-- Create Indexes for Performance
CREATE INDEX idx_sales_date        ON sales(sale_date);
CREATE INDEX idx_sales_product     ON sales(product_id);
CREATE INDEX idx_sales_category    ON sales(category);
CREATE INDEX idx_inventory_product ON inventory(product_id);
CREATE INDEX idx_inventory_date    ON inventory(record_date);


-- ================================================================
-- SECTION 2: REVENUE & SALES PERFORMANCE ANALYSIS
-- ================================================================

-- Q2.1: Monthly Revenue Trend
SELECT
    TO_CHAR(sale_date, 'Month YYYY')   AS month,
    DATE_TRUNC('month', sale_date)      AS month_start,
    COUNT(sale_id)                      AS total_transactions,
    SUM(units_sold)                     AS total_units,
    ROUND(SUM(revenue), 2)              AS total_revenue,
    ROUND(SUM(cogs), 2)                 AS total_cogs,
    ROUND(SUM(revenue - cogs), 2)       AS gross_profit,
    ROUND(SUM(revenue - cogs) / SUM(revenue) * 100, 2) AS margin_pct
FROM sales
GROUP BY 1, 2
ORDER BY 2;


-- Q2.2: Category-Wise Revenue Share
SELECT
    category,
    COUNT(DISTINCT product_id)              AS products,
    SUM(units_sold)                         AS units_sold,
    ROUND(SUM(revenue), 2)                  AS revenue,
    ROUND(SUM(revenue) / SUM(SUM(revenue)) OVER () * 100, 2) AS revenue_share_pct,
    ROUND(SUM(revenue - cogs), 2)           AS gross_profit,
    ROUND(SUM(revenue - cogs) / SUM(revenue) * 100, 2) AS margin_pct
FROM sales
GROUP BY category
ORDER BY revenue DESC;


-- Q2.3: Top 15 Revenue-Generating Products
SELECT
    s.product_id,
    s.product_name,
    s.category,
    SUM(s.units_sold)                   AS total_units,
    ROUND(SUM(s.revenue), 2)            AS total_revenue,
    ROUND(SUM(s.revenue - s.cogs), 2)   AS gross_profit,
    ROUND(AVG(s.unit_price), 2)         AS avg_selling_price,
    p.unit_cost,
    ROUND((p.selling_price - p.unit_cost)/p.selling_price * 100, 2) AS margin_pct
FROM sales s
JOIN products p ON s.product_id = p.product_id
GROUP BY s.product_id, s.product_name, s.category, p.unit_cost, p.selling_price
ORDER BY total_revenue DESC
LIMIT 15;


-- Q2.4: Week-over-Week Sales Velocity (for trend detection)
SELECT
    product_id,
    product_name,
    DATE_TRUNC('week', sale_date)   AS week_start,
    SUM(units_sold)                 AS weekly_units,
    ROUND(SUM(revenue), 2)          AS weekly_revenue,
    LAG(SUM(units_sold)) OVER (
        PARTITION BY product_id 
        ORDER BY DATE_TRUNC('week', sale_date)
    )                               AS prev_week_units,
    ROUND(
        (SUM(units_sold) - LAG(SUM(units_sold)) OVER (
            PARTITION BY product_id 
            ORDER BY DATE_TRUNC('week', sale_date))
        ) / NULLIF(LAG(SUM(units_sold)) OVER (
            PARTITION BY product_id 
            ORDER BY DATE_TRUNC('week', sale_date)), 0) * 100, 2
    )                               AS wow_growth_pct
FROM sales
GROUP BY product_id, product_name, DATE_TRUNC('week', sale_date)
ORDER BY product_id, week_start;


-- ================================================================
-- SECTION 3: ABC ANALYSIS (PARETO CLASSIFICATION)
-- ================================================================

-- Q3.1: ABC Classification by Revenue
WITH product_revenue AS (
    SELECT
        s.product_id,
        s.product_name,
        s.category,
        ROUND(SUM(s.revenue), 2)    AS total_revenue,
        SUM(s.units_sold)           AS total_units
    FROM sales s
    GROUP BY s.product_id, s.product_name, s.category
),
ranked AS (
    SELECT
        *,
        ROUND(total_revenue / SUM(total_revenue) OVER () * 100, 3)     AS revenue_pct,
        ROUND(SUM(total_revenue) OVER (ORDER BY total_revenue DESC
              ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) 
              / SUM(total_revenue) OVER () * 100, 3)                    AS cumulative_pct
    FROM product_revenue
)
SELECT
    product_id,
    product_name,
    category,
    total_revenue,
    revenue_pct,
    cumulative_pct,
    total_units,
    CASE
        WHEN cumulative_pct <= 70 THEN 'A'   -- Top 70% revenue
        WHEN cumulative_pct <= 90 THEN 'B'   -- Next 20% revenue  
        ELSE 'C'                              -- Bottom 10% revenue
    END AS abc_class
FROM ranked
ORDER BY total_revenue DESC;


-- Q3.2: ABC Summary Statistics
WITH abc_classified AS (
    -- (embed above CTE query here)
    SELECT
        product_id, product_name, category,
        SUM(revenue) AS total_revenue,
        CASE WHEN SUM(SUM(revenue)) OVER (ORDER BY SUM(revenue) DESC
             ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) / 
             SUM(SUM(revenue)) OVER () * 100 <= 70 THEN 'A'
             WHEN SUM(SUM(revenue)) OVER (ORDER BY SUM(revenue) DESC
             ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) / 
             SUM(SUM(revenue)) OVER () * 100 <= 90 THEN 'B'
             ELSE 'C' END AS abc_class
    FROM sales
    GROUP BY product_id, product_name, category
)
SELECT
    abc_class,
    COUNT(product_id)                                       AS product_count,
    ROUND(SUM(total_revenue), 2)                            AS revenue,
    ROUND(SUM(total_revenue)/SUM(SUM(total_revenue)) OVER () * 100, 2) AS rev_share_pct,
    ROUND(COUNT(product_id)::DECIMAL / SUM(COUNT(product_id)) OVER () * 100, 2) AS product_share_pct
FROM abc_classified
GROUP BY abc_class
ORDER BY abc_class;


-- ================================================================
-- SECTION 4: STOCKOUT DETECTION & RISK ANALYSIS
-- ================================================================

-- Q4.1: Products with High Stockout Risk (Zero Stock Days)
SELECT
    i.product_id,
    p.product_name,
    p.category,
    COUNT(CASE WHEN i.stockout_flag = 1 THEN 1 END)    AS stockout_days,
    ROUND(COUNT(CASE WHEN i.stockout_flag = 1 THEN 1 END)::DECIMAL / 
          COUNT(*) * 100, 2)                             AS stockout_pct,
    ROUND(AVG(i.closing_stock), 0)                       AS avg_closing_stock,
    MIN(i.closing_stock)                                 AS min_stock,
    p.reorder_point,
    p.safety_stock,
    ROUND(SUM(s.revenue), 2)                             AS revenue_at_risk
FROM inventory i
JOIN products p ON i.product_id = p.product_id
LEFT JOIN sales s ON s.product_id = i.product_id
GROUP BY i.product_id, p.product_name, p.category, p.reorder_point, p.safety_stock
HAVING COUNT(CASE WHEN i.stockout_flag = 1 THEN 1 END) > 5
ORDER BY stockout_days DESC;


-- Q4.2: Estimated Revenue Lost Due to Stockouts
WITH daily_avg AS (
    SELECT
        product_id,
        ROUND(SUM(units_sold)::DECIMAL / 184, 3)    AS avg_daily_units,
        ROUND(AVG(unit_price), 2)                    AS avg_price
    FROM sales
    GROUP BY product_id
),
stockout_count AS (
    SELECT
        product_id,
        COUNT(*) FILTER (WHERE stockout_flag = 1)   AS stockout_days
    FROM inventory
    GROUP BY product_id
)
SELECT
    sc.product_id,
    p.product_name,
    p.category,
    sc.stockout_days,
    da.avg_daily_units,
    da.avg_price,
    ROUND(sc.stockout_days * da.avg_daily_units * da.avg_price, 2) AS estimated_revenue_loss
FROM stockout_count sc
JOIN daily_avg da ON sc.product_id = da.product_id
JOIN products p ON sc.product_id = p.product_id
WHERE sc.stockout_days > 0
ORDER BY estimated_revenue_loss DESC;


-- Q4.3: Current Inventory Below Reorder Point
SELECT
    i.product_id,
    p.product_name,
    p.category,
    latest.closing_stock     AS current_stock,
    p.reorder_point,
    p.safety_stock,
    p.lead_time_days,
    p.reorder_point - latest.closing_stock  AS stock_deficit,
    CASE
        WHEN latest.closing_stock = 0           THEN '🔴 OUT OF STOCK'
        WHEN latest.closing_stock < p.safety_stock  THEN '🔴 CRITICAL — Below Safety Stock'
        WHEN latest.closing_stock < p.reorder_point THEN '🟡 REORDER NOW'
        ELSE '🟢 ADEQUATE'
    END AS reorder_status
FROM (
    SELECT product_id, closing_stock,
           ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY record_date DESC) AS rn
    FROM inventory
) latest
JOIN inventory i ON i.product_id = latest.product_id
JOIN products p ON p.product_id = latest.product_id
WHERE latest.rn = 1
ORDER BY stock_deficit DESC;


-- ================================================================
-- SECTION 5: OVERSTOCK DETECTION
-- ================================================================

-- Q5.1: Overstock Products — Capital Blocked Analysis
SELECT
    i.product_id,
    p.product_name,
    p.category,
    ROUND(AVG(i.closing_stock), 0)          AS avg_stock,
    p.max_stock_level,
    ROUND(AVG(i.closing_stock) - p.max_stock_level * 0.7, 0) AS excess_units,
    p.unit_cost,
    ROUND((AVG(i.closing_stock) - p.max_stock_level * 0.7) * p.unit_cost, 2) AS capital_blocked,
    ROUND(SUM(s.units_sold)::DECIMAL / 184, 2) AS avg_daily_sales,
    ROUND(NULLIF(AVG(i.closing_stock), 0) / 
          NULLIF(SUM(s.units_sold)::DECIMAL / 184, 0), 1) AS days_of_supply
FROM inventory i
JOIN products p ON i.product_id = p.product_id
LEFT JOIN sales s ON s.product_id = i.product_id
GROUP BY i.product_id, p.product_name, p.category, p.max_stock_level, p.unit_cost
HAVING AVG(i.closing_stock) > p.max_stock_level * 0.7
ORDER BY capital_blocked DESC
LIMIT 15;


-- Q5.2: Overstock Trend (Monthly)
SELECT
    TO_CHAR(i.record_date, 'Month YYYY')    AS month,
    COUNT(CASE WHEN i.overstock_flag = 1 THEN 1 END)   AS overstock_incidents,
    COUNT(CASE WHEN i.stockout_flag = 1 THEN 1 END)    AS stockout_incidents,
    ROUND(AVG(i.closing_stock), 1)          AS avg_inventory_level,
    SUM(i.closing_stock * p.unit_cost)      AS total_inventory_value
FROM inventory i
JOIN products p ON i.product_id = p.product_id
GROUP BY 1, DATE_TRUNC('month', i.record_date)
ORDER BY DATE_TRUNC('month', i.record_date);


-- ================================================================
-- SECTION 6: REORDER POINT OPTIMIZATION
-- ================================================================

-- Q6.1: Optimal Reorder Point Calculation (ROP = Avg Daily Demand × Lead Time + Safety Stock)
WITH demand_stats AS (
    SELECT
        product_id,
        ROUND(SUM(units_sold)::DECIMAL / 184, 3)        AS avg_daily_demand,
        ROUND(STDDEV(units_sold), 3)                     AS demand_stddev,
        MAX(units_sold)                                  AS max_daily_demand
    FROM sales
    GROUP BY product_id
)
SELECT
    p.product_id,
    p.product_name,
    p.category,
    ROUND(d.avg_daily_demand, 2)                         AS avg_daily_demand,
    p.lead_time_days,
    p.safety_stock,
    p.reorder_point                                      AS current_rop,
    -- Optimal ROP formula: (Avg Demand × Lead Time) + Safety Stock
    ROUND(d.avg_daily_demand * p.lead_time_days + p.safety_stock, 0) AS optimal_rop,
    -- EOQ: sqrt(2 × Annual Demand × Ordering Cost / Holding Cost per unit)
    ROUND(SQRT(2 * d.avg_daily_demand * 365 * 500 / (0.20 * p.unit_cost)), 0) AS eoq_units,
    CASE
        WHEN ROUND(d.avg_daily_demand * p.lead_time_days + p.safety_stock, 0) > p.reorder_point + 10
            THEN '⬆ Increase ROP'
        WHEN ROUND(d.avg_daily_demand * p.lead_time_days + p.safety_stock, 0) < p.reorder_point - 10
            THEN '⬇ Decrease ROP'
        ELSE '✓ Optimal'
    END AS adjustment_recommendation
FROM products p
JOIN demand_stats d ON p.product_id = d.product_id
ORDER BY p.category, p.product_name;


-- Q6.2: Category-Level Reorder Statistics
SELECT
    p.category,
    COUNT(p.product_id)                             AS products,
    ROUND(AVG(d.avg_daily_demand), 2)               AS avg_daily_demand,
    ROUND(AVG(p.lead_time_days), 1)                 AS avg_lead_time,
    ROUND(AVG(p.safety_stock), 0)                   AS avg_safety_stock,
    ROUND(AVG(p.reorder_point), 0)                  AS avg_current_rop,
    ROUND(AVG(d.avg_daily_demand * p.lead_time_days + p.safety_stock), 0) AS avg_optimal_rop
FROM products p
JOIN (
    SELECT product_id, ROUND(SUM(units_sold)::DECIMAL/184, 3) AS avg_daily_demand
    FROM sales GROUP BY product_id
) d ON p.product_id = d.product_id
GROUP BY p.category
ORDER BY avg_daily_demand DESC;


-- ================================================================
-- SECTION 7: BUSINESS IMPACT QUERIES
-- ================================================================

-- Q7.1: Total Revenue Loss from Stockouts (All 6 Months)
WITH daily_rates AS (
    SELECT product_id,
           SUM(units_sold)::DECIMAL / 184    AS avg_daily_units,
           AVG(unit_price)                   AS avg_price
    FROM sales GROUP BY product_id
)
SELECT
    ROUND(SUM(i.stockout_flag * dr.avg_daily_units * dr.avg_price), 2) AS total_revenue_lost,
    SUM(i.stockout_flag)                                                 AS total_stockout_days,
    COUNT(DISTINCT i.product_id) FILTER (WHERE i.stockout_flag = 1)     AS affected_products
FROM inventory i
JOIN daily_rates dr ON i.product_id = dr.product_id;


-- Q7.2: Capital Freed After Overstock Clearance
SELECT
    ROUND(SUM(excess_capital), 2)   AS total_capital_freed,
    COUNT(*)                         AS overstock_products_cleared
FROM (
    SELECT
        i.product_id,
        GREATEST(0, (AVG(i.closing_stock) - p.max_stock_level * 0.7) * p.unit_cost) AS excess_capital
    FROM inventory i JOIN products p ON i.product_id = p.product_id
    GROUP BY i.product_id, p.max_stock_level, p.unit_cost
    HAVING AVG(i.closing_stock) > p.max_stock_level * 0.7
) sub;


-- Q7.3: Product Availability Rate (% of days with stock > 0)
SELECT
    p.category,
    p.product_name,
    ROUND(
        COUNT(*) FILTER (WHERE i.closing_stock > 0)::DECIMAL / COUNT(*) * 100, 2
    ) AS availability_rate_pct,
    COUNT(*) FILTER (WHERE i.stockout_flag = 1)  AS stockout_days,
    COUNT(*)                                      AS total_days
FROM inventory i
JOIN products p ON i.product_id = p.product_id
GROUP BY p.category, p.product_name
ORDER BY availability_rate_pct;


-- Q7.4: Overall Project Business Impact Summary
SELECT
    'Revenue @ Risk (Stockouts)'        AS metric,
    CONCAT('₹', ROUND(
        (SELECT SUM(stockout_flag * avg_daily * avg_price)
         FROM inventory i
         JOIN (SELECT product_id, SUM(units_sold)/184.0 AS avg_daily, AVG(unit_price) AS avg_price 
               FROM sales GROUP BY product_id) d ON i.product_id = d.product_id
    )/100000, 2), ' Lakhs')             AS value
UNION ALL
SELECT 'Capital Tied in Overstock',
    CONCAT('₹', ROUND(
        (SELECT SUM(GREATEST(0,(avg_stock - max_stock_level*0.7)*unit_cost))
         FROM (SELECT i.product_id, AVG(i.closing_stock) AS avg_stock, 
                      p.max_stock_level, p.unit_cost
               FROM inventory i JOIN products p ON i.product_id=p.product_id
               GROUP BY i.product_id, p.max_stock_level, p.unit_cost) sub
    )/100000, 2), ' Lakhs')
UNION ALL
SELECT 'Products with Stockout Risk (>15 days)', 
    CAST(COUNT(DISTINCT product_id) FILTER (
        WHERE stockout_days > 15) AS VARCHAR)
    FROM (SELECT product_id, SUM(stockout_flag) AS stockout_days 
          FROM inventory GROUP BY product_id) x
UNION ALL
SELECT 'Avg Product Availability',
    CONCAT(ROUND(
        COUNT(*) FILTER (WHERE closing_stock > 0)::DECIMAL / COUNT(*) * 100, 1
    ), '%') FROM inventory;

