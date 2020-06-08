DEFAULT_DATAKITCHEN_URL = 'https://cloud.datakitchen.io'
KITCHEN = 'kitchen'
RECIPE = 'recipe'
VARIATION = 'variation'
PARAMETERS = 'parameters'
ORDER_ID = 'order_id'
ORDER_RUN_ID = 'order_run_id'
ORDER_RUN_STATUS = 'order_run_status'
OVERRIDES = 'recipeoverrides'

# API HTTP Request Methods
API_GET = 'get'
API_POST = 'post'
API_PUT = 'put'

# Order run status options
PLANNED_SERVING = 'PLANNED_SERVING'
ACTIVE_SERVING = 'ACTIVE_SERVING'
COMPLETED_SERVING = 'COMPLETED_SERVING'
STOPPED_SERVING = 'STOPPED_SERVING'
SERVING_ERROR = 'SERVING_ERROR'
SERVING_RERAN = 'SERVING_RERAN'
STOPPED_STATUS_TYPES = [COMPLETED_SERVING, STOPPED_SERVING, SERVING_ERROR, SERVING_RERAN]

# Vault
DEFAULT_VAULT_URL = 'https://vault2.datakitchen.io:8200'
