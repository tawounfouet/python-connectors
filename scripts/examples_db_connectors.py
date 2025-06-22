"""
Exemples d'utilisation des nouveaux connecteurs de base de données.
"""

from connectors import create_connector, list_available_connectors

def example_mysql():
    """Exemple d'utilisation du connecteur MySQL."""
    print("=== Exemple MySQL ===")
    
    config = {
        'host': 'localhost',
        'port': 3306,
        'database': 'test_db',
        'username': 'root',
        'password': 'password',
        'ssl_enabled': False,
        'timeout': 30
    }
    
    try:
        # Créer le connecteur
        mysql_conn = create_connector('mysql', config, 'mysql_instance')
        
        # Test de connexion
        with mysql_conn.connection():
            # Créer une table d'exemple
            mysql_conn.create_table('users', {
                'id': 'INT AUTO_INCREMENT PRIMARY KEY',
                'name': 'VARCHAR(100)',
                'email': 'VARCHAR(150)'
            })
            
            # Insérer des données
            mysql_conn.insert_data('users', {
                'name': 'John Doe',
                'email': 'john@example.com'
            })
            
            # Récupérer des données
            users = mysql_conn.fetch_all("SELECT * FROM users")
            print(f"Users: {users}")
            
            # Informations sur la table
            table_info = mysql_conn.get_table_info('users')
            print(f"Table info: {table_info}")
            
        print("MySQL example completed successfully!")
        
    except Exception as e:
        print(f"MySQL example failed: {e}")


def example_sqlserver():
    """Exemple d'utilisation du connecteur SQL Server."""
    print("\n=== Exemple SQL Server ===")
    
    config = {
        'host': 'localhost',
        'port': 1433,
        'database': 'test_db',
        'username': 'sa',
        'password': 'YourPassword123',
        'ssl_enabled': True,
        'timeout': 30
    }
    
    try:
        # Créer le connecteur
        sql_conn = create_connector('sqlserver', config, 'sqlserver_instance')
        
        # Test de connexion
        with sql_conn.connection():
            # Créer une table d'exemple
            sql_conn.create_table('products', {
                'id': 'INT IDENTITY(1,1) PRIMARY KEY',
                'name': 'NVARCHAR(100)',
                'price': 'DECIMAL(10,2)'
            })
            
            # Insérer des données
            sql_conn.insert_data('products', {
                'name': 'Product A',
                'price': 19.99
            })
            
            # Récupérer des données
            products = sql_conn.fetch_all("SELECT * FROM products")
            print(f"Products: {products}")
            
            # Informations sur la table
            table_info = sql_conn.get_table_info('products')
            print(f"Table info: {table_info}")
            
        print("SQL Server example completed successfully!")
        
    except Exception as e:
        print(f"SQL Server example failed: {e}")


def example_snowflake():
    """Exemple d'utilisation du connecteur Snowflake."""
    print("\n=== Exemple Snowflake ===")
    
    config = {
        'account': 'your-account',
        'username': 'your-username',
        'password': 'your-password',
        'warehouse': 'COMPUTE_WH',
        'database': 'TEST_DB',
        'schema': 'PUBLIC',
        'role': 'ACCOUNTADMIN',
        'timeout': 60
    }
    
    try:
        # Créer le connecteur
        snow_conn = create_connector('snowflake', config, 'snowflake_instance')
        
        # Test de connexion
        with snow_conn.connection():
            # Créer une table d'exemple
            snow_conn.create_table('customers', {
                'id': 'INTEGER AUTOINCREMENT',
                'name': 'VARCHAR(100)',
                'region': 'VARCHAR(50)',
                'created_at': 'TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()'
            })
            
            # Insérer des données
            snow_conn.insert_data('customers', {
                'name': 'Customer A',
                'region': 'North America'
            })
            
            # Récupérer des données
            customers = snow_conn.fetch_all("SELECT * FROM customers")
            print(f"Customers: {customers}")
            
            # Fonctionnalités spécifiques à Snowflake
            warehouses = snow_conn.get_warehouses()
            print(f"Available warehouses: {warehouses}")
            
            databases = snow_conn.get_databases()
            print(f"Available databases: {databases}")
            
            schemas = snow_conn.get_schemas()
            print(f"Available schemas: {schemas}")
            
        print("Snowflake example completed successfully!")
        
    except Exception as e:
        print(f"Snowflake example failed: {e}")


def show_available_connectors():
    """Affiche tous les connecteurs disponibles."""
    print("=== Connecteurs disponibles ===")
    connectors = list_available_connectors()
    for name, class_name in connectors.items():
        print(f"- {name}: {class_name}")


if __name__ == "__main__":
    print("Exemples d'utilisation des connecteurs de base de données")
    print("=" * 60)
    
    # Afficher les connecteurs disponibles
    show_available_connectors()
    
    # Exécuter les exemples (commentés car ils nécessitent des bases de données configurées)
    # example_mysql()
    # example_sqlserver()
    # example_snowflake()
    
    print("\nNote: Les exemples sont commentés car ils nécessitent des bases de données configurées.")
    print("Décommentez les appels de fonction pour tester avec vos propres configurations.")
