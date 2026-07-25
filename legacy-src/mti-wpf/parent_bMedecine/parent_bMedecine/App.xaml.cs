using GalaSoft.MvvmLight;
using parent_bMedecine.ViewModel;
using System.Windows;

namespace parent_bMedecine
{
    /// <summary>
    /// Logique d'interaction pour App.xaml
    /// </summary>
    public partial class App : Application
    {
        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);

            // On ViewModelLocator creation no instance of ViewModels are running, they are only registered.
            // In order to receive the message sent on Login, I need to instantiate these two VM.
            // I know it's not pretty, but it works !
            // Contact me at aparenton@gmail.com if you know a better solution, thanks !
            Application.Current.Resources["Locator"] = new ViewModelLocator();
            ViewModelBase usersViewModel = ((ViewModelLocator)Application.Current.Resources["Locator"]).UsersViewModel;
            ViewModelBase patientsViewModel = ((ViewModelLocator)Application.Current.Resources["Locator"]).PatientsViewModel;
        }
    }
}