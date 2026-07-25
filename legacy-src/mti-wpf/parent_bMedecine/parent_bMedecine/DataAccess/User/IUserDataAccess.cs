using System.Collections.Generic;

namespace parent_bMedecine.DataAccess.User
{
    /// <summary>
    /// IUserDataAccess interface
    /// </summary>
    public interface IUserDataAccess
    {
        /// <summary>
        /// Get all Users as a List
        /// </summary>
        /// <returns>a list of Users</returns>
        List<ServiceUser.User> GetListUser();

        /// <summary>
        /// Get a specific User by login
        /// </summary>
        /// <param name="login">user's login</param>
        /// <returns>the user or null</returns>
        ServiceUser.User GetUser(string login);

        /// <summary>
        /// Add a new User
        /// </summary>
        /// <param name="user">the new user</param>
        /// <returns>true if added, false otherwise</returns>
        bool AddUser(ServiceUser.User user);

        /// <summary>
        /// Delete the user
        /// </summary>
        /// <param name="login">the user's login to delete</param>
        /// <returns>true if deleted, false otherwise</returns>
        bool DeleteUser(string login);

        /// <summary>
        /// Connect a user with login/password
        /// </summary>
        /// <param name="login">user's login</param>
        /// <param name="pwd">user's password</param>
        /// <returns>true if connected, false otherwise</returns>
        bool Connect(string login, string pwd);

        /// <summary>
        /// Disconnect a user with login
        /// </summary>
        /// <param name="login">user's login</param>
        void Disconnect(string login);

        /// <summary>
        /// Get a user's role with login
        /// </summary>
        /// <param name="login">user's login</param>
        /// <returns>role as a string, empty string otherwise</returns>
        string GetRole(string login);
    }
}