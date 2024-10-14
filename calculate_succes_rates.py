# llama-405b React
# Overall Success Rate: 50.00%
# Results for React-Opt:
# Rewards: [14, 9, 11, 19, 7, 7]
# Counts: [24, 31, 23, 21, 18, 17]

## llama 405b ReSPact
# Overall Success Rate: 67.16%
# Results for Respact-Opt:
# Rewards: [18, 20, 18, 15, 9, 10]
# Counts: [24, 31, 23, 21, 18, 17]

def calculate_success_rates(rewards, counts):
    """
    Calculate the overall success rate and per-category success rates.

    Parameters:
    rewards (list): List of rewards for each category.
    counts (list): List of counts for each category.

    Returns:
    tuple: Overall success rate and list of success rates for each category.
    """
    # Calculate overall success rate
    overall_success_rate = (sum(rewards) / sum(counts)) * 100
    
    # Calculate success rate for each category
    category_success_rates = [(rewards[i] / counts[i]) * 100 for i in range(len(rewards))]
    
    return overall_success_rate, category_success_rates
    
llama_405b_respact_rewards = [18, 20, 18, 15, 9, 10]
llama_405b_respact_counts = [24, 31, 23, 21, 18, 17]

overall_success_rate, category_success_rates = calculate_success_rates(llama_405b_respact_rewards, llama_405b_respact_counts)
breakpoint()    
print(f"Overall Success Rate: {overall_success_rate:.2f}%")
print(f"Category Success Rate: {category_success_rates:.2f}%")