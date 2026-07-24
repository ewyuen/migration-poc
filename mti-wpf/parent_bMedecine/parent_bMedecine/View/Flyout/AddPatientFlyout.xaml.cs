using System.Windows;
using System.Windows.Controls;

namespace parent_bMedecine.View.Flyout
{
    /// <summary>
    /// Logique d'interaction pour AddPatientFlyout.xaml
    /// </summary>
    public partial class AddPatientFlyout : UserControl
    {
        public AddPatientFlyout()
        {
            InitializeComponent();
        }

        /// <summary>
        /// Open patient panel
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void AddPatient_Click(object sender, RoutedEventArgs e)
        {
            MainWindow parentWindow = (MainWindow)Window.GetWindow(this);
            parentWindow.ToggleFlyout(1);
        }
    }
}