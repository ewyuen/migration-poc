using System;
using System.Globalization;
using System.Windows.Data;

namespace parent_bMedecine.Utilities.Converters
{
    /// <summary>
    /// Class to convert boolean value to Visibility value as string ("Collapsed" or "Visible")
    /// </summary>
    [ValueConversion(typeof(bool), typeof(string))]
    public class BoolToVisibilityConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if ((bool)value)
                return "Collapsed";
            else
                return "Visible";
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotSupportedException();
        }
    }
}