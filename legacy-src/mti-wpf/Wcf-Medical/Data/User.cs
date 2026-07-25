using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Interfaces;
using System.IO;
using System.Web.Hosting;
using System.ComponentModel.Composition;

namespace Data
{
    [Export(typeof(Interfaces.IUser))]
    [ExportMetadata("type", "student")]
    public class User : IUser
    {
        /// <summary>
        /// crée la liste des 4 users
        /// </summary>
        /// <returns>retourne la liste de users</returns>
        public List<Dbo.User> CreateListUser()
        {
            List<Dbo.User> res = new List<Dbo.User>();

            Dbo.User user1 = new Dbo.User()
            {
                Firstname = "gregory",
                Login = "greg",
                Name = "house",
                Pwd = "greg",
                Role = "Medecin",
                Connected = false
            };

            user1.Picture = LoadUserPicture("medecin.jpg");

            Dbo.User user2 = new Dbo.User()
            {
                Firstname = "fréderic",
                Login = "fred",
                Name = "ducelier",
                Pwd = "fred",
                Role = "Chirurgien",
                Connected = false
            };

            user2.Picture = LoadUserPicture("chirurgien.jpg");

            Dbo.User user3 = new Dbo.User()
            {
                Firstname = "Laura",
                Login = "laura",
                Name = "dupont",
                Pwd = "laura",
                Role = "Infirmière",
                Connected = false
            };

            user3.Picture = LoadUserPicture("infirmiere.jpg");

            Dbo.User user4 = new Dbo.User()
            {
                Firstname = "Albert",
                Login = "albert",
                Name = "Einstein",
                Pwd = "albert",
                Role = "Radiologue",
                Connected = false
            };

            user4.Picture = LoadUserPicture("radiologue.jpg");

            res.Add(user1);
            res.Add(user2);
            res.Add(user3);
            res.Add(user4);

            return res;
        }

        private byte[] LoadUserPicture(string filename)
        {
            try
            {
                string picturePath = System.IO.Path.Combine(HostingEnvironment.ApplicationPhysicalPath, "Pictures", "Users", filename);
                if (System.IO.File.Exists(picturePath))
                {
                    return System.IO.File.ReadAllBytes(picturePath);
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error loading picture {filename}: {ex.Message}");
            }
            return new byte[0];
        }

    }
}
