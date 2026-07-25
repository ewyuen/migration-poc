using GalaSoft.MvvmLight;
using GalaSoft.MvvmLight.Ioc;
using Microsoft.Practices.ServiceLocation;
using parent_bMedecine.BusinessManagement.Observation;
using parent_bMedecine.BusinessManagement.Patient;
using parent_bMedecine.BusinessManagement.User;
using parent_bMedecine.DataAccess.Observation;
using parent_bMedecine.DataAccess.Patient;
using parent_bMedecine.DataAccess.User;
using parent_bMedecine.ViewModel.FlyoutViewModel;

namespace parent_bMedecine.ViewModel
{
    /// <summary>
    /// This class contains static references to all the view models in the
    /// application and provides an entry point for the bindings.
    /// </summary>
    public class ViewModelLocator
    {
        /// <summary>
        /// Initializes a new instance of the ViewModelLocator class.
        /// </summary>
        public ViewModelLocator()
        {
            ServiceLocator.SetLocatorProvider(() => SimpleIoc.Default);

            if (!ViewModelBase.IsInDesignModeStatic)
            {
                // DataAccess
                SimpleIoc.Default.Register<IUserDataAccess, UserDataAccess>();
                SimpleIoc.Default.Register<IPatientDataAccess, PatientDataAccess>();
                SimpleIoc.Default.Register<IObservationDataAccess, ObservationDataAccess>();
            }

            // DataServices
            SimpleIoc.Default.Register<IUserDataService, UserDataService>();
            SimpleIoc.Default.Register<IPatientDataService, PatientDataService>();
            SimpleIoc.Default.Register<IObservationDataService, ObservationDataService>();

            // Window ViewModel
            SimpleIoc.Default.Register<MainViewModel>();

            // UserControl ViewModels
            SimpleIoc.Default.Register<MainTabControlViewModel>();
            SimpleIoc.Default.Register<HomeViewModel>();
            SimpleIoc.Default.Register<LoginViewModel>();
            SimpleIoc.Default.Register<PatientsViewModel>();
            SimpleIoc.Default.Register<ObservationsViewModel>();
            SimpleIoc.Default.Register<UsersViewModel>();

            // Flyouts ViewModels
            SimpleIoc.Default.Register<AddUserViewModel>();
            SimpleIoc.Default.Register<AddPatientViewModel>();
            SimpleIoc.Default.Register<AddObservationViewModel>();
        }

        #region Properties

        public MainViewModel MainViewModel
        {
            get
            {
                return ServiceLocator.Current.GetInstance<MainViewModel>();
            }
        }

        public MainTabControlViewModel MainTabControlViewModel
        {
            get
            {
                return ServiceLocator.Current.GetInstance<MainTabControlViewModel>();
            }
        }

        public HomeViewModel HomeViewModel
        {
            get
            {
                return ServiceLocator.Current.GetInstance<HomeViewModel>();
            }
        }

        public LoginViewModel LoginViewModel
        {
            get
            {
                return ServiceLocator.Current.GetInstance<LoginViewModel>();
            }
        }

        public PatientsViewModel PatientsViewModel
        {
            get
            {
                return ServiceLocator.Current.GetInstance<PatientsViewModel>();
            }
        }

        public ObservationsViewModel ObservationsViewModel
        {
            get
            {
                return ServiceLocator.Current.GetInstance<ObservationsViewModel>();
            }
        }

        public UsersViewModel UsersViewModel
        {
            get
            {
                return ServiceLocator.Current.GetInstance<UsersViewModel>();
            }
        }

        public AddUserViewModel AddUserViewModel
        {
            get
            {
                return ServiceLocator.Current.GetInstance<AddUserViewModel>();
            }
        }

        public AddPatientViewModel AddPatientViewModel
        {
            get
            {
                return ServiceLocator.Current.GetInstance<AddPatientViewModel>();
            }
        }

        public AddObservationViewModel AddObservationViewModel
        {
            get
            {
                return ServiceLocator.Current.GetInstance<AddObservationViewModel>();
            }
        }

        #endregion Properties

        public static void Cleanup()
        {
            // DataAccess
            SimpleIoc.Default.Unregister<IUserDataAccess>();
            SimpleIoc.Default.Unregister<IPatientDataAccess>();
            SimpleIoc.Default.Unregister<IObservationDataAccess>();

            // DataServices
            SimpleIoc.Default.Unregister<IUserDataService>();
            SimpleIoc.Default.Unregister<IPatientDataService>();
            SimpleIoc.Default.Unregister<IObservationDataService>();

            // ViewModels
            SimpleIoc.Default.Unregister<MainViewModel>();
            SimpleIoc.Default.Unregister<MainTabControlViewModel>();
            SimpleIoc.Default.Unregister<HomeViewModel>();
            SimpleIoc.Default.Unregister<LoginViewModel>();
            SimpleIoc.Default.Unregister<PatientsViewModel>();
            SimpleIoc.Default.Unregister<ObservationsViewModel>();
            SimpleIoc.Default.Unregister<UsersViewModel>();
            SimpleIoc.Default.Unregister<AddUserViewModel>();
            SimpleIoc.Default.Unregister<AddPatientViewModel>();
            SimpleIoc.Default.Unregister<AddObservationViewModel>();
        }
    }
}