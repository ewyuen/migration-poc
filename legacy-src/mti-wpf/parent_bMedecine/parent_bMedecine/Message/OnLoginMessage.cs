using GalaSoft.MvvmLight.Messaging;

namespace parent_bMedecine.Message
{
    /// <summary>
    /// Message sent to ViewModels when the user logs in
    /// </summary>
    public class OnLoginMessage : MessageBase
    {
        #region Properties

        /// <summary>
        /// Current user account name
        /// </summary>
        public string UserAccountName { get; set; }

        /// <summary>
        /// True if user has a readonly role like "Infirmiere"
        /// False otherwise (such as "Medecin")
        /// </summary>
        public bool ReadOnlyUserProfile { get; set; }

        #endregion Properties

        /// <summary>
        /// Constructor
        /// </summary>
        /// <param name="userAccountName">current user account name</param>
        /// <param name="isReadOnlyUserProfile">if user has a readonly role</param>
        public OnLoginMessage(string userAccountName, bool isReadOnlyUserProfile)
        {
            UserAccountName = userAccountName;
            ReadOnlyUserProfile = isReadOnlyUserProfile;
        }
    }
}