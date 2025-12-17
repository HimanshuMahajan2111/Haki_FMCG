"""
Database Indexing and Optimization
Creates indexes and optimizes queries for production performance
"""
from sqlalchemy import Index, text
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


def create_performance_indexes(db: Session):
    """Create indexes for optimal query performance"""
    
    indexes = [
        # RFP table indexes
        "CREATE INDEX IF NOT EXISTS idx_rfp_customer_id ON rfps(customer_id)",
        "CREATE INDEX IF NOT EXISTS idx_rfp_status ON rfps(status)",
        "CREATE INDEX IF NOT EXISTS idx_rfp_created_at ON rfps(created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_rfp_priority ON rfps(priority)",
        "CREATE INDEX IF NOT EXISTS idx_rfp_customer_status ON rfps(customer_id, status)",
        
        # Product table indexes
        "CREATE INDEX IF NOT EXISTS idx_product_category ON products(category)",
        "CREATE INDEX IF NOT EXISTS idx_product_manufacturer ON products(manufacturer)",
        "CREATE INDEX IF NOT EXISTS idx_product_price ON products(price)",
        "CREATE INDEX IF NOT EXISTS idx_product_in_stock ON products(in_stock)",
        "CREATE INDEX IF NOT EXISTS idx_product_name ON products(name)",
        "CREATE INDEX IF NOT EXISTS idx_product_code ON products(code)",
        "CREATE INDEX IF NOT EXISTS idx_product_category_stock ON products(category, in_stock)",
        
        # WorkflowRun table indexes
        "CREATE INDEX IF NOT EXISTS idx_workflow_status ON workflow_runs(status)",
        "CREATE INDEX IF NOT EXISTS idx_workflow_created_at ON workflow_runs(created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_workflow_rfp_id ON workflow_runs(rfp_id)",
        "CREATE INDEX IF NOT EXISTS idx_workflow_customer_id ON workflow_runs(customer_id)",
        "CREATE INDEX IF NOT EXISTS idx_workflow_completed_at ON workflow_runs(completed_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_workflow_status_created ON workflow_runs(status, created_at DESC)",
        
        # AgentLog table indexes
        "CREATE INDEX IF NOT EXISTS idx_agent_log_workflow_id ON agent_logs(workflow_id)",
        "CREATE INDEX IF NOT EXISTS idx_agent_log_agent_name ON agent_logs(agent_name)",
        "CREATE INDEX IF NOT EXISTS idx_agent_log_timestamp ON agent_logs(timestamp DESC)",
        "CREATE INDEX IF NOT EXISTS idx_agent_log_status ON agent_logs(status)",
        "CREATE INDEX IF NOT EXISTS idx_agent_log_action ON agent_logs(action)",
        
        # Composite indexes for common queries
        "CREATE INDEX IF NOT EXISTS idx_workflow_customer_status_created ON workflow_runs(customer_id, status, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_product_category_price ON products(category, price)",
        
        # Full-text search indexes (PostgreSQL)
        # "CREATE INDEX IF NOT EXISTS idx_product_name_fts ON products USING gin(to_tsvector('english', name))",
        # "CREATE INDEX IF NOT EXISTS idx_product_description_fts ON products USING gin(to_tsvector('english', description))",
    ]
    
    logger.info("Creating performance indexes...")
    
    for index_sql in indexes:
        try:
            db.execute(text(index_sql))
            logger.info(f"Created index: {index_sql}")
        except Exception as e:
            logger.warning(f"Failed to create index: {index_sql}. Error: {e}")
    
    db.commit()
    logger.info("Index creation completed")


def analyze_query_performance(db: Session):
    """Analyze and optimize query performance"""
    
    # Update table statistics
    tables = ['rfps', 'products', 'workflow_runs', 'agent_logs']
    
    logger.info("Analyzing table statistics...")
    
    for table in tables:
        try:
            db.execute(text(f"ANALYZE {table}"))
            logger.info(f"Analyzed table: {table}")
        except Exception as e:
            logger.warning(f"Failed to analyze table {table}: {e}")
    
    db.commit()


def optimize_database(db: Session):
    """Run database optimization tasks"""
    
    logger.info("Running database optimization...")
    
    try:
        # Vacuum and analyze (SQLite doesn't support VACUUM in transaction)
        db.commit()  # Commit any pending transactions
        
        # For PostgreSQL
        # db.execute(text("VACUUM ANALYZE"))
        
        # For SQLite
        db.execute(text("VACUUM"))
        db.execute(text("ANALYZE"))
        
        logger.info("Database optimization completed")
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")


def get_query_execution_plan(db: Session, query: str) -> dict:
    """Get query execution plan for optimization"""
    
    try:
        # For PostgreSQL: EXPLAIN ANALYZE
        # For SQLite: EXPLAIN QUERY PLAN
        result = db.execute(text(f"EXPLAIN QUERY PLAN {query}"))
        
        plan = [dict(row) for row in result]
        return {'query': query, 'plan': plan}
    except Exception as e:
        return {'query': query, 'error': str(e)}


def create_materialized_views(db: Session):
    """Create materialized views for common analytics queries"""
    
    views = [
        # Daily workflow statistics
        """
        CREATE VIEW IF NOT EXISTS vw_daily_workflow_stats AS
        SELECT 
            DATE(created_at) as date,
            status,
            COUNT(*) as count,
            AVG(duration_seconds) as avg_duration
        FROM workflow_runs
        GROUP BY DATE(created_at), status
        """,
        
        # Customer performance
        """
        CREATE VIEW IF NOT EXISTS vw_customer_performance AS
        SELECT 
            customer_id,
            COUNT(*) as total_rfps,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_rfps,
            AVG(duration_seconds) as avg_duration
        FROM workflow_runs
        GROUP BY customer_id
        """,
        
        # Product popularity
        """
        CREATE VIEW IF NOT EXISTS vw_product_popularity AS
        SELECT 
            category,
            COUNT(*) as product_count,
            AVG(price) as avg_price,
            SUM(CASE WHEN in_stock = 1 THEN 1 ELSE 0 END) as in_stock_count
        FROM products
        GROUP BY category
        """
    ]
    
    logger.info("Creating materialized views...")
    
    for view_sql in views:
        try:
            db.execute(text(view_sql))
            logger.info("Created view")
        except Exception as e:
            logger.warning(f"Failed to create view: {e}")
    
    db.commit()


# Query optimization hints
OPTIMIZED_QUERIES = {
    'get_recent_workflows': """
        SELECT * FROM workflow_runs 
        WHERE created_at >= :start_date 
        ORDER BY created_at DESC 
        LIMIT :limit
    """,
    
    'get_customer_workflows': """
        SELECT * FROM workflow_runs 
        WHERE customer_id = :customer_id 
        AND status = :status
        ORDER BY created_at DESC
    """,
    
    'search_products': """
        SELECT * FROM products 
        WHERE category = :category 
        AND in_stock = 1
        AND price BETWEEN :min_price AND :max_price
        ORDER BY price ASC
        LIMIT :limit
    """,
    
    'get_agent_performance': """
        SELECT 
            agent_name,
            COUNT(*) as total_actions,
            AVG(duration) as avg_duration,
            SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_actions
        FROM agent_logs
        WHERE timestamp >= :start_date
        GROUP BY agent_name
        ORDER BY total_actions DESC
    """
}
