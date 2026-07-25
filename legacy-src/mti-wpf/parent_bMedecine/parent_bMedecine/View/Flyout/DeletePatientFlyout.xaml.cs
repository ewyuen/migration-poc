using System.Windows;
using System.Windows.Controls;

namespace parent_bMedecine.View.Flyout
{
    /// <summary>
    /// Logique d'interaction pour DeletePatientFlyout.xaml
    /// </summary>
    public partial class DeletePatientFlyout : UserControl
    {
        public DeletePatientFlyout()
        {
            InitializeComponent();
        }

        /// <summary>
        /// Close user panel
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void NoButton_Click(object sender, RoutedEventArgs e)
        {
            MainWindow parentWindow = (MainWindow)Window.GetWindow(this);
            parentWindow.ToggleFlyout(3);
        }
    }
}