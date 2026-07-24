using System.Collections.Generic;

namespace parent_bMedecine.BusinessManagement.User
{
    /// <summary>
    /// UserDataService class
    /// </summary>
    public class UserDataService : IUserDataService
    {
        /// <summary>
        /// DataAccess object
        /// </summary>
        private readonly DataAccess.User.IUserDataAccess _userDataAccess;

        /// <summary>
        /// Constructor
        /// </summary>
        /// <param name="userDataAccess">injected by SimpleIoC, see ViewModelLocator</param>
        public UserDataService(DataAccess.User.IUserDataAccess userDataAccess)
        {
            _userDataAccess = userDataAccess;
        }

        public List<ServiceUser.User> GetListUser()
        {
            return _userDataAccess.GetListUser();
        }

        public ServiceUser.User GetUser(string login)
        {
            return _userDataAccess.GetUser(login);
        }

        public bool AddUser(ServiceUser.User user)
        {
            return _userDataAccess.AddUser(user);
        }

        public bool DeleteUser(string login)
        {
            return _userDataAccess.DeleteUser(login);
        }

        public bool Connect(string login, string pwd)
        {
            return _userDataAccess.Connect(login, pwd);
        }

        public void Disconnect(string login)
        {
            _userDataAccess.Disconnect(login);
        }

        public string GetRole(string login)
        {
            return _userDataAccess.GetRole(login);
        }
    }
}