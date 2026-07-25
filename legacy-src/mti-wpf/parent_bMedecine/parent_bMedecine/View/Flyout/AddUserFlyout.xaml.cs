using System.Windows;
using System.Windows.Controls;

namespace parent_bMedecine.View.Flyout
{
    /// <summary>
    /// Logique d'interaction pour AddUserFlyout.xaml
    /// </summary>
    public partial class AddUserFlyout : UserControl
    {
        public AddUserFlyout()
        {
            InitializeComponent();
        }

        /// <summary>
        /// Open user panel
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void AddUser_Click(object sender, RoutedEventArgs e)
        {
            MainWindow parentWindow = (MainWindow)Window.GetWindow(this);
            parentWindow.ToggleFlyout(0);
        }
    }
}