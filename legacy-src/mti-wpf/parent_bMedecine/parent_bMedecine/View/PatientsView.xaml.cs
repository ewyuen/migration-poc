using System.Windows;
using System.Windows.Controls;

namespace parent_bMedecine.View
{
    /// <summary>
    /// Logique d'interaction pour PatientsView.xaml
    /// </summary>
    public partial class PatientsView : UserControl
    {
        public PatientsView()
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

        /// <summary>
        /// Open observation panel
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void AddObservation_Click(object sender, RoutedEventArgs e)
        {
            MainWindow parentWindow = (MainWindow)Window.GetWindow(this);
            parentWindow.ToggleFlyout(2);
        }

        /// <summary>
        /// Open patient deletion panel
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void DeletePatient_Click(object sender, RoutedEventArgs e)
        {
            MainWindow parentWindow = (MainWindow)Window.GetWindow(this);
            parentWindow.ToggleFlyout(3);
        }
    }
}