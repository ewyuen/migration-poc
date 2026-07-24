using System;
using System.Collections.Generic;
using System.Diagnostics;

namespace parent_bMedecine.DataAccess.User
{
    /// <summary>
    /// UserDataAccess class
    /// </summary>
    public class UserDataAccess : IUserDataAccess
    {
        public List<ServiceUser.User> GetListUser()
        {
            ServiceUser.ServiceUserClient client = new ServiceUser.ServiceUserClient();
            List<ServiceUser.User> res;

            try
            {
                res = client.GetListUser();
                client.Close();
            }
            catch (Exception ex)
            {
                Debug.WriteLine("UserDataAccess: GetListUser: Exception:" + ex.Message);
                res = null;
            }

            return res;
        }

        public ServiceUser.User GetUser(string login)
        {
            ServiceUser.ServiceUserClient client = new ServiceUser.ServiceUserClient();
            ServiceUser.User res;

            try
            {
                res = client.GetUser(login);
                client.Close();
            }
            catch (Exception ex)
            {
                Debug.WriteLine("UserDataAccess: GetUser: Exception:" + ex.Message);
                res = null;
            }

            return res;
        }

        public bool AddUser(ServiceUser.User user)
        {
            ServiceUser.ServiceUserClient client = new ServiceUser.ServiceUserClient();
            bool res;

            try
            {
                res = client.AddUser(user);
                client.Close();
            }
            catch (Exception ex)
            {
                Debug.WriteLine("UserDataAccess: AddUser: Exception:" + ex.Message);
                res = false;
            }

            return res;
        }

        public bool DeleteUser(string login)
        {
            ServiceUser.ServiceUserClient client = new ServiceUser.ServiceUserClient();
            bool res;

            try
            {
                res = client.DeleteUser(login);
                client.Close();
            }
            catch (Exception ex)
            {
                Debug.WriteLine("UserDataAccess: DeleteUser: Exception:" + ex.Message);
                res = false;
            }

            return res;
        }

        public bool Connect(string login, string pwd)
        {
            ServiceUser.ServiceUserClient client = new ServiceUser.ServiceUserClient();
            bool res;

            try
            {
                res = client.Connect(login, pwd);
                client.Close();
            }
            catch (Exception ex)
            {
                Debug.WriteLine("UserDataAccess: Connect: Exception:" + ex.Message);
                res = false;
            }

            return res;
        }

        public void Disconnect(string login)
        {
            ServiceUser.ServiceUserClient client = new ServiceUser.ServiceUserClient();

            try
            {
                client.Disconnect(login);
                client.Close();
            }
            catch (Exception ex)
            {
                Debug.WriteLine("UserDataAccess: Disconnect: Exception:" + ex.Message);
            }
        }

        public string GetRole(string login)
        {
            ServiceUser.ServiceUserClient client = new ServiceUser.ServiceUserClient();
            string res;

            try
            {
                res = client.GetRole(login);
                client.Close();
            }
            catch (Exception ex)
            {
                Debug.WriteLine("UserDataAccess: GetRole: Exception:" + ex.Message);
                res = "";
            }

            return res;
        }
    }
}