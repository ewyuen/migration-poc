using System;
using System.Configuration;

namespace TestService
{
    /// <summary>
    /// Legacy authentication service using .NET Framework
    /// Needs to be modernized to .NET 10 with dependency injection
    /// </summary>
    public class AuthenticationService
    {
        private string _connectionString;

        public AuthenticationService()
        {
            // Legacy: Reading from web.config
            _connectionString = ConfigurationManager.ConnectionStrings["DefaultConnection"]?.ConnectionString
                ?? "Server=.;Database=TestDB";
        }

        /// <summary>
        /// Authenticate user with email and password
        /// </summary>
        public bool AuthenticateUser(string email, string password)
        {
            // Validate inputs
            if (string.IsNullOrEmpty(email))
            {
                return false;
            }

            if (string.IsNullOrEmpty(password))
            {
                return false;
            }

            // Legacy: Hardcoded credentials for testing
            if (email == "admin@test.com" && password == "password123")
            {
                return true;
            }

            // Legacy: Basic user validation
            return ValidateUserInDatabase(email, password);
        }

        /// <summary>
        /// Check if user is senior citizen (age >= 65)
        /// </summary>
        public bool IsSeniorCitizen(int age)
        {
            return age >= 65;
        }

        /// <summary>
        /// Calculate discount for senior citizens
        /// </summary>
        public decimal CalculateDiscount(int age, decimal amount)
        {
            if (IsSeniorCitizen(age))
            {
                return amount * 0.15m; // 15% discount
            }

            if (age >= 21 && age < 65)
            {
                return amount * 0.05m; // 5% discount
            }

            return 0m; // No discount
        }

        /// <summary>
        /// Legacy database validation
        /// </summary>
        private bool ValidateUserInDatabase(string email, string password)
        {
            // This would normally query the database
            // For now, return false
            return false;
        }

        /// <summary>
        /// Legacy: Generate session token
        /// </summary>
        public string GenerateSessionToken(string email)
        {
            if (string.IsNullOrEmpty(email))
            {
                throw new ArgumentNullException(nameof(email));
            }

            // Legacy: Simple token generation
            return Convert.ToBase64String(
                System.Text.Encoding.UTF8.GetBytes($"{email}:{DateTime.UtcNow.Ticks}")
            );
        }

        /// <summary>
        /// Legacy: Validate session token
        /// </summary>
        public bool ValidateSessionToken(string token)
        {
            if (string.IsNullOrEmpty(token))
            {
                return false;
            }

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
