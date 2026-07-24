using System;
using System.Globalization;
using System.Windows.Data;

namespace parent_bMedecine.Utilities.Converters
{
    /// <summary>
    /// Class to convert boolean value to status string "Connecté" or "Déconnecté".
    /// Used for tooltips in User DataGrid
    /// </summary>
    [ValueConversion(typeof(bool), typeof(string))]
    public class BoolToStringConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if ((bool)value)
                return "Connecté";
            else
                return "Déconnecté";
        }

        public object ConvertBack(object value, Type targetType,
        object parameter, CultureInfo culture)
        {
            throw new NotSupportedException();
        }
    }
}