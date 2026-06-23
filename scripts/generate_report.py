import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Environment and directory setup
load_dotenv()
DATABASE_URL = os.getenv("NEON_DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("NEON_DATABASE_URL not found in environment variables.")

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

engine = create_engine(DATABASE_URL)


# =====================================================================
# CUSTOMER RFM MODULE
# =====================================================================

def fetch_rfm_data():
    """Queries database to extract and rank raw customer RFM metrics."""
    print("Fetching customer RFM datasets...")
    query = """
    WITH database_anchor AS (
        SELECT MAX("orderDate"::date) AS max_db_date FROM orders
    ),
    rfm_base AS (
        SELECT 
            c."companyName",
            (SELECT max_db_date FROM database_anchor) - MAX(o."orderDate"::date) AS recency,
            COUNT(DISTINCT o."orderID") AS frequency,
            SUM(od."unitPrice" * od.quantity * (1.0 - od.discount)) AS monetary
        FROM customers c
        JOIN orders o ON c."customerID" = o."customerID"
        JOIN order_details od ON o."orderID" = od."orderID"
        GROUP BY c."companyName"
    )
    SELECT 
        "companyName", recency, frequency, ROUND(monetary::numeric, 2) AS monetary,
        NTILE(5) OVER (ORDER BY recency DESC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
    FROM rfm_base;
    """
    return pd.read_sql(query, con=engine)


def segment_customers(df):
    """Categorizes accounts based on quantitative RFM index patterns."""
    print("Applying account segmentation logic...")
    def label_rfm_segment(row):
        r, f, m = row['r_score'], row['f_score'], row['m_score']
        if r >= 4 and f >= 4 and m >= 4: return 'Champions'
        elif r <= 2 and (f >= 4 or m >= 4): return "At Risk / Can't Lose"
        elif f >= 3 and m >= 3: return 'Loyal Customers'
        elif r >= 4 and f <= 2: return 'New Customers'
        else: return 'Hibernating'

    df['segment'] = df.apply(label_rfm_segment, axis=1)
    return df


def save_rfm_scatter_map(df):
    """Generates an optimized scatter plot using a log-scale and pointer callouts."""
    print("Generating adjusted RFM scatter map...")
    plt.figure(figsize=(11, 7))
    sns.set_theme(style="whitegrid")
    
    ax = sns.scatterplot(
        x='recency', 
        y='monetary', 
        hue='segment', 
        style='segment',
        data=df, 
        palette='Set1', 
        s=120, 
        alpha=0.8,
        edgecolor='w',
        linewidth=0.8
    )
    
    ax.set_yscale('log')
    plt.gca().invert_xaxis()
    
    label_offsets = {
        'QUICK-Stop': (35, 25),
        'Ernst Handel': (-45, 30),
        'Save-a-lot Markets': (40, -25)
    }
    
    for idx, row in df.iterrows():
        name = row['companyName']
        if name in label_offsets:
            offset_x, offset_y = label_offsets[name]
            ax.annotate(
                name,
                xy=(row['recency'], row['monetary']),
                xytext=(offset_x, offset_y),
                textcoords='offset points',
                arrowprops=dict(arrowstyle="->", color='black', lw=0.7),
                bbox=dict(boxstyle="round,pad=0.2", fc="white", edgecolor="gray", alpha=0.85, lw=0.5),
                fontsize=9,
                fontweight='semibold'
            )
            
    plt.title('Northwind Customer Segmentation: Value vs. Recency', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Recency (Days Since Last Order — Most Recent on Right)', fontsize=11, labelpad=10)
    plt.ylabel('Total Monetary Spend ($, Logarithmic Scale)', fontsize=11, labelpad=10)
    
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f'${x:,.0f}'))
    plt.legend(title='Customer Segment', bbox_to_anchor=(1.02, 1), loc='upper left')
    
    plot_path = os.path.join(OUTPUT_DIR, 'customer_segmentation_map.png')
    plt.tight_layout()
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved optimized scatter map to: {plot_path}")


def save_segment_profile_heatmap(df):
    """Computes and visualizes core metric averages across segments."""
    print("Generating executive segment behavior profiles...")
    profile_summary = df.groupby('segment')[['recency', 'frequency', 'monetary']].mean()
    profile_summary.columns = ['Avg Recency (Days)', 'Avg Frequency (Orders)', 'Avg Spend ($)']
    
    plt.figure(figsize=(10, 5))
    sns.heatmap(
        profile_summary, 
        annot=True, 
        fmt=",.1f", 
        cmap="Blues", 
        linewidths=1.5,
        cbar=False
    )
    
    plt.title('Customer Segment Behavioral Profiles (Averages)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Core Operational Metrics', fontsize=11, labelpad=10)
    plt.ylabel('Customer Segment', fontsize=11)
    plt.xticks(rotation=0)
    
    plot_path = os.path.join(OUTPUT_DIR, 'segment_behavior_profiles.png')
    plt.tight_layout()
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved segment overview chart to: {plot_path}")


def export_roster_report(df):
    """Compiles and saves categorical account distribution rosters as Markdown."""
    report_path = os.path.join(OUTPUT_DIR, 'customer_roster_report.md')
    print(f"Compiling structured text rosters to: {report_path}")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Northwind Active Customer Roster Report\n\n")
        
        grouped = df.groupby('segment')
        for segment_name, group in grouped:
            f.write(f"## Segment: {segment_name.upper()} ({len(group)} Companies)\n")
            f.write("| Company Name | Lifetime Spend | RFM Score |\n")
            f.write("| :--- | :--- | :--- |\n")
            
            sorted_group = group.sort_values(by='monetary', ascending=False)
            for _, row in sorted_group.iterrows():
                f.write(f"| {row['companyName']} | ${row['monetary']:,.2f} | R:{row['r_score']} F:{row['f_score']} M:{row['m_score']} |\n")
            f.write("\n")


# =====================================================================
# PRODUCT PERFORMANCE MODULE
# =====================================================================

def generate_product_revenue_report(engine):
    """Processes gross product distributions and generates performance visuals."""
    print("Processing product performance metrics...")
    query_top_products = """
    SELECT 
        p."productName",
        SUM(od."unitPrice" * od."quantity" * (1.0 - od."discount")) AS total_revenue
    FROM order_details od
    JOIN products p ON od."productID" = p."productID"
    GROUP BY p."productName"
    ORDER BY total_revenue DESC
    LIMIT 10;
    """
    df_top_products = pd.read_sql(query_top_products, con=engine)
    df_top_products.rename(columns={'productName': 'Product Name', 'total_revenue': 'Total Revenue'}, inplace=True)
    df_top_products.set_index('Product Name', inplace=True)
    
    csv_path = os.path.join(OUTPUT_DIR, 'top_products_revenue.csv')
    df_top_products.to_csv(csv_path)
    print(f"Saved product dataset to: {csv_path}")

    plt.figure(figsize=(12, 6))
    sns.set_theme(style="whitegrid")
    ax = sns.barplot(x=df_top_products['Total Revenue'], y=df_top_products.index, data=df_top_products, palette='viridis')
    plt.title('Top 10 Products by Total Revenue', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Total Revenue ($)', fontsize=14, labelpad=10)
    plt.ylabel('Product Name', fontsize=14, labelpad=10)

    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f'${x:,.2f}'))
    sns.despine(left=True, bottom=True)
    
    plot_path = os.path.join(OUTPUT_DIR, 'top_products_revenue.png')
    plt.tight_layout()
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved product chart to: {plot_path}")


# =====================================================================
# SUPPLY CHAIN & LOGISTICS MODULE
# =====================================================================

def generate_shipping_delays_report(engine):
    """Evaluates regional fulfillment velocity and structural latency profiles."""
    print("Evaluating logistics metrics and latency...")
    query_shipping_delays = """
    SELECT 
        "shipCountry",
        COUNT("orderID") AS total_orders,
        ROUND(AVG("shippedDate"::date - "orderDate"::date), 2) AS avg_days_to_ship,
        SUM(CASE WHEN "shippedDate" > "requiredDate" THEN 1 ELSE 0 END) AS late_shipments
    FROM orders
    WHERE "shippedDate" IS NOT NULL
    GROUP BY "shipCountry"
    ORDER BY avg_days_to_ship DESC;
    """
    df_shipping_delays = pd.read_sql(query_shipping_delays, con=engine)
    df_shipping_delays.rename(columns={
        'shipCountry': 'Ship Country', 
        'total_orders': 'Total Orders', 
        'avg_days_to_ship': 'Avg Days to Ship', 
        'late_shipments': 'Late Shipments'
    }, inplace=True)
    
    csv_path = os.path.join(OUTPUT_DIR, 'shipping_delays_by_country.csv')
    df_shipping_delays.to_csv(csv_path, index=False)
    print(f"Saved logistics dataset to: {csv_path}")

    df_top_delays = df_shipping_delays.sort_values(by='Avg Days to Ship', ascending=False).head(10)
    df_top_delays.set_index('Ship Country', inplace=True)

    plt.figure(figsize=(12, 6))
    sns.set_theme(style="whitegrid")
    ax = sns.barplot(x=df_top_delays['Avg Days to Ship'], y=df_top_delays.index, data=df_top_delays, palette='coolwarm')  
    plt.title("Top 10 Countries by Average Shipping Delay", fontsize=16, fontweight='bold', pad=20)
    plt.xlabel("Average Days to Ship", fontsize=14, labelpad=10) 
    plt.ylabel("Country", fontsize=14, labelpad=10)  
    
    for container in ax.containers:
        ax.bar_label(container, fmt='%.2f', label_type='edge', fontsize=10, padding=3)

    sns.despine(left=True, bottom=True)
    
    plot_path = os.path.join(OUTPUT_DIR, 'shipping_latency_delays.png')
    plt.tight_layout()
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved logistics chart to: {plot_path}")


# =====================================================================
# ADVANCED RISK ASSESSMENT MODULE (NEW)
# =====================================================================

def evaluate_business_risk(df_customer, engine):
    """Calculates revenue concentration metrics and logs systemic vulnerabilities."""
    print("Executing automated corporate risk evaluation...")
    
    # 1. Calculate Customer Concentration Risk (HHI)
    total_cust_rev = df_customer['monetary'].sum()
    df_customer['revenue_share'] = (df_customer['monetary'] / total_cust_rev) * 100
    customer_hhi = (df_customer['revenue_share'] ** 2).sum()
    
    # 2. Extract and Calculate Product Concentration Risk (HHI)
    product_query = """
    SELECT 
        p."productName",
        SUM(od."unitPrice" * od."quantity" * (1.0 - od."discount")) AS total_revenue
    FROM order_details od
    JOIN products p ON od."productID" = p."productID"
    GROUP BY p."productName";
    """
    df_product = pd.read_sql(product_query, con=engine)
    total_prod_rev = df_product['total_revenue'].sum()
    df_product['revenue_share'] = (df_product['total_revenue'] / total_prod_rev) * 100
    product_hhi = (df_product['revenue_share'] ** 2).sum()
    
    # 3. Identify Concentration Threshold Violations (Whales > 10% Share)
    customer_whales = df_customer[df_customer['revenue_share'] >= 10.0].sort_values(by='revenue_share', ascending=False)
    product_whales = df_product[df_product['revenue_share'] >= 10.0].sort_values(by='revenue_share', ascending=False)
    
    # 4. Identify Logistics Hotspots (Countries where over 15% of shipments are late)
    logistics_query = """
    SELECT 
        "shipCountry",
        COUNT("orderID") AS total_orders,
        SUM(CASE WHEN "shippedDate" > "requiredDate" THEN 1 ELSE 0 END) AS late_orders
    FROM orders
    WHERE "shippedDate" IS NOT NULL
    GROUP BY "shipCountry";
    """
    df_logistics = pd.read_sql(logistics_query, con=engine)
    df_logistics['late_rate'] = (df_logistics['late_orders'] / df_logistics['total_orders']) * 100
    logistics_hotspots = df_logistics[df_logistics['late_rate'] >= 15.0].sort_values(by='late_rate', ascending=False)
    
    # 5. Write Briefing Report to Disk
    report_path = os.path.join(OUTPUT_DIR, 'executive_risk_summary.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Northwind Corporate Risk Assessment Summary\n\n")
        
        # Section A: Inflow Concentration
        f.write("## 1. Portfolio Revenue Concentration\n")
        f.write("Concentration metrics utilize the Herfindahl-Hirschman Index (HHI). Scores over 1,500 signal structural dependency, and scores over 2,500 signal extreme asset vulnerability.\n\n")
        
        f.write(f"- **Customer Account HHI:** {customer_hhi:.2f} — ")
        f.write("HIGH CONCENTRATION\n" if customer_hhi > 2500 else "MODERATE CONCENTRATION\n" if customer_hhi > 1500 else "HEALTHY DIVERSIFICATION\n")
        
        f.write(f"- **Product Inventory HHI:** {product_hhi:.2f} — ")
        f.write("HIGH CONCENTRATION\n" if product_hhi > 2500 else "MODERATE CONCENTRATION\n" if product_hhi > 1500 else "HEALTHY DIVERSIFICATION\n")
        f.write("\n")
        
        # Section B: Singular Key Dependencies
        f.write("## 2. High-Exposure Inflow Single Points of Failure\n")
        f.write("Accounts or individual products generating more than 10% of total company inflows:\n\n")
        
        f.write("### Exposure Accounts\n")
        if not customer_whales.empty:
            f.write("| Account Name | Lifetime Value | Revenue Share |\n| :--- | :--- | :--- |\n")
            for _, row in customer_whales.iterrows():
                f.write(f"| {row['companyName']} | ${row['monetary']:,.2f} | {row['revenue_share']:.2f}% |\n")
        else:
            f.write("No single customer account exceeds the 10% revenue risk threshold.\n")
        f.write("\n")
        
        f.write("### Exposure Inventory Lines\n")
        if not product_whales.empty:
            f.write("| Product Name | Gross Revenue | Revenue Share |\n| :--- | :--- | :--- |\n")
            for _, row in product_whales.iterrows():
                f.write(f"| {row['productName']} | ${row['total_revenue']:,.2f} | {row['revenue_share']:.2f}% |\n")
        else:
            f.write("No single product inventory line exceeds the 10% revenue risk threshold.\n")
        f.write("\n")
        
        # Section C: Supply Chain Failures
        f.write("## 3. Supply Chain Fulfillment Anomalies\n")
        f.write("Target trade corridors where late fulfillment metrics cross operational failure thresholds (>= 15% late rate):\n\n")
        if not logistics_hotspots.empty:
            f.write("| Ship Country | Completed Shipments | Late Deliveries | Breach Rate |\n| :--- | :--- | :--- | :--- |\n")
            for _, row in logistics_hotspots.iterrows():
                f.write(f"| {row['shipCountry']} | {int(row['total_orders'])} | {int(row['late_orders'])} | {row['late_rate']:.2f}% |\n")
        else:
            f.write("All shipping corridors remain within acceptable delivery window margins.\n")
            
    print(f"Saved executive risk summary report to: {report_path}")


# =====================================================================
# ORCHESTRATION ENGINE
# =====================================================================

def main():
    print("Initiating corporate BI reporting pipeline run...")
    try:
        df_raw = fetch_rfm_data()
        df_segmented = segment_customers(df_raw)
        
        csv_path = os.path.join(OUTPUT_DIR, 'rfm_customer_segments.csv')
        df_segmented.to_csv(csv_path, index=False)
        print(f"Saved structural database tables to: {csv_path}")
        
        save_rfm_scatter_map(df_segmented)
        save_segment_profile_heatmap(df_segmented)
        export_roster_report(df_segmented)
        
        generate_product_revenue_report(engine)
        generate_shipping_delays_report(engine)
        
        # Execute the new business risk evaluation engine
        evaluate_business_risk(df_segmented, engine)
        
        print("\nPipeline execution complete. Deliverables successfully written to output disk.")
    except Exception as e:
        print(f"Execution Error: Corporate report pipeline failed: {e}")

if __name__ == "__main__":
    main()