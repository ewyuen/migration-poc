using GalaSoft.MvvmLight;
using GalaSoft.MvvmLight.Command;
using parent_bMedecine.BusinessManagement.Observation;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Windows;

namespace parent_bMedecine.ViewModel.FlyoutViewModel
{
    /// <summary>
    /// AddObservationViewModel class for AddObservationFlyout
    /// </summary>
    public class AddObservationViewModel : ViewModelBase
    {
        #region Members

        private readonly IObservationDataService _observationDataService;
        private ServicePatient.Patient _selectedPatient;
        private DateTime _date = DateTime.Now;
        private int _weight;
        private int _bloodpressure;
        private string _comment = string.Empty;
        private string _prescription = string.Empty;
        private ObservableCollection<string> _pictures = new ObservableCollection<string>();
        private ObservableCollection<string> _prescriptions = new ObservableCollection<string>();

        #endregion Members

        #region Properties

        /// <summary>
        /// Selected patient by user
        /// </summary>
        public ServicePatient.Patient SelectedPatient
        {
            get { return _selectedPatient; }
            set
            {
                _selectedPatient = value;
                RaisePropertyChanged("SelectedPatient");
            }
        }

        /// <summary>
        /// Observation date
        /// </summary>
        public DateTime Date
        {
            get { return _date; }
            set
            {
                _date = value;
                RaisePropertyChanged("Date");
            }
        }

        /// <summary>
        /// Patient weight
        /// </summary>
        public int Weight
        {
            get { return _weight; }
            set
            {
                _weight = value;
                RaisePropertyChanged("Weight");
            }
        }

        /// <summary>
        /// Patient blood pressure
        /// </summary>
        public int BloodPressure
        {
            get { return _bloodpressure; }
            set
            {
                _bloodpressure = value;
                RaisePropertyChanged("BloodPressure");
            }
        }

        /// <summary>
        /// Observation comment
        /// </summary>
        public string Comment
        {
            get { return _comment; }
            set
            {
                _comment = value;
                RaisePropertyChanged("Comment");
            }
        }

        /// <summary>
        /// Observation prescription
        /// </summary>
        public string Prescription
        {
            get { return _prescription; }
            set
            {
                _prescription = value;
                RaisePropertyChanged("Prescription");
            }
        }

        /// <summary>
        /// Observation pictures
        /// </summary>
        public ObservableCollection<string> Pictures
        {
            get { return _pictures; }
            set { _pictures = value; }
        }

        /// <summary>
        /// Observation prescriptions
        /// </summary>
        public ObservableCollection<string> Prescriptions
        {
            get { return _prescriptions; }
            set { _prescriptions = value; }
        }

        public RelayCommand AddObservationCommand { get; private set; }

        public RelayCommand AddObservationPictureCommand { get; private set; }

        public RelayCommand AddObservationPrescriptionCommand { get; private set; }

        public RelayCommand<int> DeleteObservationPictureCommand { get; private set; }

        public RelayCommand<int> DeleteObservationPrescriptionCommand { get; private set; }

        #endregion Properties

        #region Constructors

        /// <summary>
        /// Constructor
        /// </summary>
        public AddObservationViewModel(IObservationDataService observationDataService)
        {
            // DataService
            _observationDataService = observationDataService;

            // Messages
            MessengerInstance.Register<Message.OnPatientSelectionMessage>(this, m => { SelectedPatient = m.SelectedPatient; });

            // Commands
            AddObservationCommand = new RelayCommand(AddObservationExecute);
            AddObservationPictureCommand = new RelayCommand(AddObservationPictureExecute);
            AddObservationPrescriptionCommand = new RelayCommand(AddObservationPrescriptionExecute);
            DeleteObservationPictureCommand = new RelayCommand<int>(i => DeleteObservationPictureExecute(i));
            DeleteObservationPrescriptionCommand = new RelayCommand<int>(i => DeleteObservationPrescriptionExecute(i));
        }

        #endregion Constructors

        #region Methods

        /// <summary>
        /// Create observation object and call web service to add it
        /// </summary>
        private void AddObservationExecute()
        {
            List<Byte[]> pictures = new List<Byte[]>();
            foreach (string picture in Pictures)
            {
                pictures.Add(Utilities.ImageManager.GetBytesFromImage(picture));
            }

            List<string> prescriptions = new List<string>();
            foreach (string prescription in Prescriptions)
            {
                prescriptions.Add(prescription);
            }

            ServiceObservation.Observation newObservation = new ServiceObservation.Observation()
            {
                BloodPressure = _bloodpressure,
                Comment = _comment,
                Date = _date,
                Pictures = pictures,
                Prescription = prescriptions,
                Weight = _weight
            };

            bool res = _observationDataService.AddObservation(_selectedPatient.Id, newObservation);
            if (res)
            {
                MessengerInstance.Send<Message.OnAddObservationMessage>(new Message.OnAddObservationMessage());
            }
            else
            {
                MessageBox.Show("Erreur lors de l'ajout de l'observation, veuillez réessayer.", "Erreur");
            }

            BloodPressure = 0;
            Weight = 0;
            Comment = string.Empty;
            Prescription = string.Empty;
            Date = DateTime.Now;
            Pictures.Clear();
            Prescriptions.Clear();
        }

        /// <summary>
        /// Open file dialog box to pick pictures for observation
        /// </summary>
        private void AddObservationPictureExecute()
        {
            Microsoft.Win32.OpenFileDialog dlg = new Microsoft.Win32.OpenFileDialog();

            dlg.Filter = "Fichiers Image|*.jpg;*.jpeg;*.png";

            // Show open file dialog box
            Nullable<bool> result = dlg.ShowDialog();

            // Process open file dialog box results
            if (result == true)
            {
                Pictures.Add(dlg.FileName);
            }
        }

        /// <summary>
        /// Add the prescription to the observation prescription list
        /// </summary>
        private void AddObservationPrescriptionExecute()
        {
            Prescriptions.Add(Prescription);
            Prescription = string.Empty;
            RaisePropertyChanged("Prescription");
        }

        /// <summary>
        /// Remove observation prescription from the list
        /// </summary>
        /// <param name="index"></param>
        private void DeleteObservationPrescriptionExecute(int index)
        {
            Prescriptions.RemoveAt(index);
        }

        /// <summary>
        /// Remove observation picture from the list
        /// </summary>
        /// <param name="index"></param>
        private void DeleteObservationPictureExecute(int index)
        {
            Pictures.RemoveAt(index);
        }

        #endregion Methods
    }
}