#!/usr/bin/env python3

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
