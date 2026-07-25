using GalaSoft.MvvmLight;
using GalaSoft.MvvmLight.Command;
using GalaSoft.MvvmLight.Ioc;
using parent_bMedecine.BusinessManagement.User;
using System;

namespace parent_bMedecine.ViewModel
{
    /// <summary>
    /// MainViewModel class for MainWindow
    /// </summary>
    public class MainViewModel : ViewModelBase
    {
        #region Members

        private readonly IUserDataService _userDataService;
        private ViewModelBase _currentViewModel = SimpleIoc.Default.GetInstance<LoginViewModel>();
        private string _userAccountName = string.Empty;
        private string _logoutButtonVisibility = "Collapsed";

        #endregion Members

        #region Properties

        /// <summary>
        /// MainViewModel currentViewModel used with DataTemplate in the MainWindow
        /// </summary>
        public ViewModelBase CurrentViewModel
        {
            get
            {
                return _currentViewModel;
            }
            set
            {
                if (_currentViewModel == value)
                    return;
                _currentViewModel = value;
                RaisePropertyChanged("CurrentViewModel");
            }
        }

        /// <summary>
        /// Current user account name
        /// </summary>
        public string UserAccountName
        {
            get
            {
                return _userAccountName;
            }
            set
            {
                _userAccountName = value;
                RaisePropertyChanged("UserAccountName");
            }
        }

        /// <summary>
        /// Logout button visibility
        /// </summary>
        public string LogoutButtonVisibility
        {
            get
            {
                return _logoutButtonVisibility;
            }
            set
            {
                _logoutButtonVisibility = value;
                RaisePropertyChanged("LogoutButtonVisibility");
            }
        }

        public RelayCommand LogoutCommand { get; private set; }

        #endregion Properties

        #region Constructors

        /// <summary>
        /// Initializes a new instance of the MainViewModel class.
        /// </summary>
        public MainViewModel(IUserDataService userDataService)
        {
            // DataService
            _userDataService = userDataService;

            // Commands
            LogoutCommand = new RelayCommand(OnLogoutExecute);

            // Messages
            MessengerInstance.Register<Message.OnLoginMessage>(this, e => { OnLoginExecute(e.UserAccountName); });
        }

        #endregion Constructors

        #region Methods

        /// <summary>
        /// Set properties on user login
        /// </summary>
        /// <param name="userAccountName"></param>
        private void OnLoginExecute(string userAccountName)
        {
            this.CurrentViewModel = SimpleIoc.Default.GetInstance<MainTabControlViewModel>();

            UserAccountName = userAccountName;
            LogoutButtonVisibility = "Visible";
        }

        /// <summary>
        /// Call web service to disconnect current user and reset properties
        /// </summary>
        private void OnLogoutExecute()
        {
            _userDataService.Disconnect(UserAccountName);

            this.CurrentViewModel = SimpleIoc.Default.GetInstance<LoginViewModel>();

            UserAccountName = String.Empty;
            LogoutButtonVisibility = "Collapsed";

            MessengerInstance.Send<Message.OnLogoutMessage>(new Message.OnLogoutMessage());
        }

        #endregion Methods
    }
}