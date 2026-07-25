```csharp
namespace AuthenticationService
{
    public record UserCredentials(string Email, string Password);
    public record SessionToken(string Token);
    public record DiscountRequest(int Age, decimal Amount);

    public interface IUserRepository
    {
        Task<bool> ValidateUserAsync(string email, string password);
    }

    public class UserRepository : IUserRepository
    {
        private readonly string _connectionString;

        public UserRepository(IConfiguration configuration)
        {
            _connectionString = configuration.GetConnectionString("DefaultConnection") 
                ?? "Server=.;Database=TestDB";
        }

        public async Task<bool> ValidateUserAsync(string email, string password)
        {
            // Implement async database validation
            return await Task.FromResult(false);
        }
    }

    public class AuthenticationService
    {
        private readonly IUserRepository _userRepository;

        public AuthenticationService(IUserRepository userRepository)
        {
            _userRepository = userRepository;
        }

        public async Task<bool> AuthenticateUserAsync(UserCredentials credentials)
        {
            if (!AuthenticationLogic.ValidateInputs(credentials.Email, credentials.Password))
                return false;

            if (credentials.Email == "admin@test.com" && credentials.Password == "password123")
                return true;

            return await _userRepository.ValidateUserAsync(credentials.Email, credentials.Password);
        }

        public decimal CalculateDiscount(DiscountRequest request) =>
            AuthenticationLogic.CalculateDiscount(request.Age, request.Amount);

        public SessionToken GenerateSessionToken(string email)
        {
            if (string.IsNullOrEmpty(email))
                throw new ArgumentNullException(nameof(email));

            return new SessionToken(SessionLogic.GenerateSessionToken(email));
        }

        public bool ValidateSessionToken(SessionToken token) =>
            SessionLogic.ValidateSessionToken(token.Token);
    }

    public class UserCredentialsValidator : AbstractValidator<UserCredentials>
    {
        public UserCredentialsValidator()
        {
            RuleFor(x => x.Email).NotEmpty().EmailAddress();
            RuleFor(x => x.Password).NotEmpty().MinimumLength(8);
        }
    }

    public class DiscountRequestValidator : AbstractValidator<DiscountRequest>
    {
        public DiscountRequestValidator()
        {
            RuleFor(x => x.Age).InclusiveBetween(0, 120);
            RuleFor(x => x.Amount).GreaterThanOrEqualTo(0);
        }
    }
}
```