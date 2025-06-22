#!/usr/bin/env python3

import sys
import os

# Ajouter le répertoire parent (racine du projet) au chemin Python
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

print("Starting test...")

try:
    from connectors.base import BaseConnector
    print("✅ Imported BaseConnector")
    
    class TestConnector(BaseConnector):
        def connect(self): 
            self._connected = True
            print('Connected!')
        def disconnect(self): 
            self._connected = False
        def test_connection(self): 
            return True
    
    print("✅ Created TestConnector")
    
    config = {'metrics_enabled': False}
    test = TestConnector(config)
    print("✅ Instantiated TestConnector")
    
    print("Testing execute_with_metrics...")
    result = test.execute_with_metrics('test', lambda: 'success')
    print(f'✅ Result: {result}')
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("Test completed.")
