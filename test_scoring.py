import math

def simulate_scores(avg_reviews, avg_rating, max_reviews_cap):
    # Current App Logic
    traffic_score = min(10.0, (math.log10(avg_reviews + 1) / math.log10(max_reviews_cap + 1)) * 10)
    
    # Adjusted Sensor Tower Logic Hypothesis
    # Sensor tower seems to have a harsher scale, and it's out of 10 but visually represented as X.X
    
    # For Traffic: 'pegasus' got 7.95 in our app but 4.4 in Sensor Tower
    # For Difficulty: 'pegasus' got 8.54 in our app but 9.0 in Sensor Tower
    
    # Let's see what inputs would generate our app's scores first
    # 7.95 = (log10(avg_reviews + 1) / 6) * 10 
    # 0.795 * 6 = 4.77 = log10(avg_reviews)
    # avg_reviews ~= 10^4.77 ~= 58,884
    
    # 8.54 = (avg_rating / 5.0) * 10 -> avg_rating = 4.27
    
    # Now, how do we get 4.4 from 58,884 reviews?
    # Sensor tower might be using a higher cap, or a different log base, or a completely different metric like search volume index.
    # Since we ONLY have reviews, we must adjust our review cap to squash the score down to ~4.4
    # 4.4 = (log10(58884) / target_log) * 10
    # 0.44 = 4.77 / target_log 
    # target_log = 4.77 / 0.44 = 10.84
    # 10^10.84 = 69,183,097,091 (way too high)
    
    # Alternative: Linear scaling after log?
    # Or just use a higher scale limit: 
    # Let's try max cap of 10,000,000,000 to match ST's harshness
    st_traffic = min(10.0, (math.log10(avg_reviews + 1) / 10.84) * 10)
    
    # Difficulty: Our app gave 8.54, ST gave 9.0
    # If avg rating is ~4.3, maybe the formula is heavier on the top end
    # Or it doesn't divide by 5, but maybe (avg_rating - 1) / 4 to expand the scale?
    # If avg = 4.3 -> (4.3 - 1) / 4 = 3.3 / 4 = 0.825 * 10 = 8.25
    # Let's try: (avg_rating * 2) - somewhat arbitrary.
    # What if Difficulty is based on top 10 rankings stability? We don't have that.
    # Let's just scale difficulty slightly up:
    st_diff = min(10.0, avg_rating * 2) # e.g. 4.5 * 2 = 9.0
    
    return st_traffic, st_diff

print("Simulating pegasus (avg 58k reviews, 4.3 rating)")
t, d = simulate_scores(58000, 4.3, 1_000_000)
print(f"Target: Traffic 4.4, Diff 9.0")
print(f"Result: Traffic {t:.2f}, Diff {d:.2f}")

print("\nSimulating adventure (avg 250k reviews, 4.7 rating)") # guess based on ST 4.8 traffic
t2, d2 = simulate_scores(250000, 4.7, 1_000_000)
print(f"Target: Traffic 4.8, Diff 9.5")
print(f"Result: Traffic {t2:.2f}, Diff {d2:.2f}")
