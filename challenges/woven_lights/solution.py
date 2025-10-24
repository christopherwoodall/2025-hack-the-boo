def count_decodings(s):
    MOD = 1000000007
    n = len(s)
    
    # Edge case: empty string or starts with 0
    if n == 0 or s[0] == '0':
        return 0
    
    # dp[i] = number of ways to decode s[0:i]
    dp = [0] * (n + 1)
    dp[0] = 1  # Empty string has one way to decode
    dp[1] = 1  # First character (non-zero) has one way
    
    for i in range(2, n + 1):
        # Current digit is s[i-1], previous digit is s[i-2]
        current = s[i-1]
        previous = s[i-2]
        
        # Try taking current digit alone
        if current != '0':
            dp[i] = (dp[i] + dp[i-1]) % MOD
        
        # Try taking previous and current as a pair
        two_digit = int(previous + current)
        if 10 <= two_digit <= 26:
            dp[i] = (dp[i] + dp[i-2]) % MOD
        
        # If dp[i] is still 0, this means we cannot decode up to position i
        # (e.g., we have an invalid sequence like "30" or "00")
        if dp[i] == 0:
            return 0
    
    return dp[n]

# Read input
s = input().strip()
print(count_decodings(s))