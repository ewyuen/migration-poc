using System.Windows;
using System.Windows.Controls;

namespace parent_bMedecine.View.Flyout
{
    /// <summary>
    /// Logique d'interaction pour AddObservationFlyout.xaml
    /// </summary>
    public partial class AddObservationFlyout : UserControl
    {
        public AddObservationFlyout()
        {
            InitializeComponent();
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
    }
}