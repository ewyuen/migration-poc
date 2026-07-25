using GalaSoft.MvvmLight;
using GalaSoft.MvvmLight.Command;
using parent_bMedecine.BusinessManagement.User;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Windows;

namespace parent_bMedecine.ViewModel
{
    /// <summary>
    /// UsersViewModel class for UsersView
    /// </summary>
    public class UsersViewModel : ViewModelBase
    {
        #region Members

        private readonly IUserDataService _userDataService;
        private ObservableCollection<ServiceUser.User> _users = new ObservableCollection<ServiceUser.User>();
        private bool _readOnlyUserProfile = false;

        #endregion Members

        #region Properties

        /// <summary>
        /// User list
        /// </summary>
        public ObservableCollection<ServiceUser.User> Users
        {
            get { return _users; }
            set { _users = value; }
        }

        /// <summary>
        /// Boolean value to know if current user is readonly or not
        /// </summary>
        public bool ReadOnlyUserProfile
        {
            get
            {
                return _readOnlyUserProfile;
            }
            set
            {
                _readOnlyUserProfile = value;
                RaisePropertyChanged("ReadOnlyUserProfile");
            }
        }

        public RelayCommand<ServiceUser.User> DeleteUserCommand { get; private set; }

        #endregion Properties

        #region Constructors

        /// <summary>
        /// Constructor
        /// </summary>
        public UsersViewModel(IUserDataService userDataService)
        {
            // DataService
            _userDataService = userDataService;

            // Commands
            DeleteUserCommand = new RelayCommand<ServiceUser.User>(u => { DeleteUserExecute(u); });

            // Messages
            MessengerInstance.Register<Message.OnLoginMessage>(this, m => { RetrieveUsers(); ReadOnlyUserProfile = m.ReadOnlyUserProfile; });
            MessengerInstance.Register<Message.OnLogoutMessage>(this, m => { Reset(); });
            MessengerInstance.Register<Message.OnAddUserMessage>(this, m => { RetrieveUsers(); });
        }

        #endregion Constructors

        #region Methods

        /// <summary>
        /// Reset view model properties
        /// </summary>
        private void Reset()
        {
            Users.Clear();
        }

        /// <summary>
        /// Retrieve users data from web service
        /// </summary>
        private void RetrieveUsers()
        {
            Users.Clear();

            List<ServiceUser.User> res = _userDataService.GetListUser();
            foreach (var user in res)
                Users.Add(user);
        }

        /// <summary>
        /// Call web service to delete user
        /// </summary>
        /// <param name="user">user to delete</param>
        private void DeleteUserExecute(ServiceUser.User user)
        {
            bool res = _userDataService.DeleteUser(user.Login);
            if (res)
            {
                Users.Remove(user);
            }
            else
            {
                MessageBox.Show("Erreur lors de la suppression de l'utilisateur, veuillez réessayer.", "Erreur");
            }
        }

        #endregion Methods
    }
}