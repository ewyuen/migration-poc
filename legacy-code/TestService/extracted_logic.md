```csharp
namespace AuthenticationDomain.Logic
{
    /// <summary>
    /// Pure domain logic for user authentication
    /// Invariant: Results depend only on inputs
    /// </summary>
    public static class AuthenticationLogic
    {
        /// <summary>
        /// Validates email and password inputs
        /// </summary>
        /// <param name="email">User's email address</param>
        /// <param name="password">User's password</param>
        /// <returns>True if inputs are valid</returns>
        public static bool ValidateInputs(string email, string password) =>
            !string.IsNullOrEmpty(email) && !string.IsNullOrEmpty(password);

        /// <summary>
        /// Determines if user is a senior citizen
        /// </summary>
        /// <param name="age">User's age</param>
        /// <returns>True if age is 65 or older</returns>
        public static bool IsSeniorCitizen(int age) => age >= 65;

        /// <summary>
        /// Calculates age-based discount
        /// </summary>
        /// <param name="age">User's age</param>
        /// <param name="amount">Original amount</param>
        /// <returns>Calculated discount</returns>
        public static decimal CalculateDiscount(int age, decimal amount) =>
            IsSeniorCitizen(age) ? amount * 0.15m :
            age >= 21 && age < 65 ? amount * 0.05m :
            0m;
    }

    /// <summary>
    /// Pure domain logic for session management
    /// Invariant: Results depend only on inputs
    /// </summary>
    public static class SessionLogic
    {
        /// <summary>
        /// Generates a session token
        /// </summary>
        /// <param name="email">User's email address</param>
        /// <returns>Base64 encoded session token</returns>
        public static string GenerateSessionToken(string email) =>
            Convert.ToBase64String(
                System.Text.Encoding.UTF8.GetBytes($"{email}:{DateTime.UtcNow.Ticks}")
            );

        /// <summary>
        /// Validates a session token
        /// </summary>
        /// <param name="token">Session token to validate</param>
        /// <returns>True if token is valid</returns>
        public static bool ValidateSessionToken(string token)
        {
            if (string.IsNullOrEmpty(token))
                return false;

            try
            {
                var decoded = System.Text.Encoding.UTF8.GetString(
                    Convert.FromBase64String(token)
                );
                return !string.IsNullOrEmpty(decoded);
            }
            catch
            {
                return false;
            }
        }
    }
}
```