using MahApps.Metro.Controls;

namespace parent_bMedecine.View
{
    /// <summary>
    /// Logique d'interaction pour MainWindow.xaml
    /// </summary>
    public partial class MainWindow : MetroWindow
    {
        public MainWindow()
        {
            InitializeComponent();
        }

        /// <summary>
        /// Simple method to toggle panel
        /// </summary>
        /// <param name="index">panel index</param>
        public void ToggleFlyout(int index)
        {
            var flyout = this.Flyouts.Items[index] as MahApps.Metro.Controls.Flyout;
            if (flyout == null)
            {
                return;
            }

            flyout.IsOpen = !flyout.IsOpen;
        }

        private void LogoutButton_Click(object sender, System.Windows.RoutedEventArgs e)
        {
            foreach (MahApps.Metro.Controls.Flyout flyout in this.Flyouts.Items)
            {
                if (flyout != null)
                    flyout.IsOpen = false;
            }
        }
    }
}