from app.services.prompt_chain_new import create_dashboard
output_file = create_dashboard('/Users/suhaaniagarwal/viz.ai/backend/data/synthetic_transport_data.csv', 'create a interactive, animated, data visualisation dashboard for best insights of this data')
print(f'Dashboard created: {output_file}')
