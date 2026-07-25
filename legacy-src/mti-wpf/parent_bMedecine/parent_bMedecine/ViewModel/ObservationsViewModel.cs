using GalaSoft.MvvmLight;
using GalaSoft.MvvmLight.Command;
using parent_bMedecine.BusinessManagement.Patient;
using parent_bMedecine.Model;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Windows;

namespace parent_bMedecine.ViewModel
{
    /// <summary>
    /// ObservationsViewModel class for ObservationsView
    /// </summary>
    public class ObservationsViewModel : ViewModelBase, ServiceLive.IServiceLiveCallback
    {
        #region Members

        private readonly IPatientDataService _patientDataService;
        private ServicePatient.Patient _selectedPatient;
        private ObservableCollection<ServicePatient.Observation> _observations = new ObservableCollection<ServicePatient.Observation>();
        private int _selectedObservationIndex;
        private ObservableCollection<byte[]> _pictureList = new ObservableCollection<byte[]>();
        private ServiceLive.ServiceLiveClient _client;
        private object selectedItem = null;

        #endregion Members

        #region Properties

        public ObservableCollection<ChartObject> Weights { get; private set; }

        public ObservableCollection<ChartObject> BloodPressures { get; private set; }

        public ObservableCollection<ChartObject> Temperatures { get; private set; }

        public ObservableCollection<ChartObject> Hearts { get; private set; }

        /// <summary>
        /// Selected patient by user
        /// </summary>
        public ServicePatient.Patient SelectedPatient
        {
            get
            {
                return _selectedPatient;
            }
            set
            {
                _selectedPatient = value;
                RaisePropertyChanged("SelectedPatient");
            }
        }

        /// <summary>
        /// Patient observation list
        /// </summary>
        public ObservableCollection<ServicePatient.Observation> Observations
        {
            get { return _observations; }
            set { _observations = value; }
        }

        /// <summary>
        /// Patient observations picture list
        /// </summary>
        public ObservableCollection<byte[]> PictureList
        {
            get { return _pictureList; }
            set { _pictureList = value; }
        }

        /// <summary>
        /// Selected observation index by user
        /// </summary>
        public int SelectedObservationIndex
        {
            get
            {
                return _selectedObservationIndex;
            }
            set
            {
                _selectedObservationIndex = value;
                RaisePropertyChanged("SelectedObservationIndex");
            }
        }

        /// <summary>
        /// Selected chart object by user for highlight
        /// </summary>
        public object SelectedItem
        {
            get { return selectedItem; }
            set { selectedItem = value; }
        }

        public RelayCommand StartServiceLiveCommand { get; private set; }

        public RelayCommand StopServiceLiveCommand { get; private set; }

        #endregion Properties

        #region Constructors

        /// <summary>
        /// Constructor
        /// </summary>
        public ObservationsViewModel(IPatientDataService patientDataService)
        {
            // DataService
            _patientDataService = patientDataService;

            // ChartObjects
            Weights = new ObservableCollection<ChartObject>();
            BloodPressures = new ObservableCollection<ChartObject>();
            Hearts = new ObservableCollection<ChartObject>();
            Temperatures = new ObservableCollection<ChartObject>();

            // Commands
            StartServiceLiveCommand = new RelayCommand(StartServiceLiveExecute);
            StopServiceLiveCommand = new RelayCommand(StopServiceLiveExecute);

            // Messages
            MessengerInstance.Register<Message.OnLogoutMessage>(this, m => { Reset(); });
            MessengerInstance.Register<Message.OnPatientSelectionMessage>(this, m => { OnPatientSelectionExecute(m.SelectedPatient); });
            MessengerInstance.Register<Message.OnAddObservationMessage>(this, m => { OnPatientSelectionExecute(SelectedPatient); });
        }

        #endregion Constructors

        #region Methods

        /// <summary>
        /// Retrieve patient observations data on selection by user
        /// </summary>
        /// <param name="patient"></param>
        private void OnPatientSelectionExecute(ServicePatient.Patient patient)
        {
            if (patient == null)
                return;

            Reset();
            SelectedPatient = patient;

            try
            {
                List<ServicePatient.Observation> res = _patientDataService.GetPatient(SelectedPatient.Id).Observations;
                res = res.OrderByDescending(o => o.Date).ToList();
                if (!res.Any())
                    MessengerInstance.Send<Message.OnPatientEmptyContent>(new Message.OnPatientEmptyContent());

                foreach (var observation in res)
                {
                    Observations.Add(observation);

                    foreach (byte[] img in observation.Pictures)
                        PictureList.Add(img);

                    Weights.Add(new ChartObject() { Category = observation.Date.ToString(), Number = observation.Weight });
                    BloodPressures.Add(new ChartObject() { Category = observation.Date.ToString(), Number = observation.BloodPressure });
                }
                SelectedObservationIndex = 0;
            }
            catch (Exception)
            {
                MessageBox.Show("Erreur lors de la récupération des observations, veuillez réessayer.", "Erreur");
            }
        }

        /// <summary>
        /// Reset the view model properties
        /// </summary>
        private void Reset()
        {
            Observations.Clear();
            PictureList.Clear();

            Weights.Clear();
            BloodPressures.Clear();
            Temperatures.Clear();
            Hearts.Clear();

            StopServiceLiveExecute();
        }

        /// <summary>
        /// Retrieve live data from duplex web service
        /// </summary>
        private void StartServiceLiveExecute()
        {
            System.ServiceModel.InstanceContext context = new System.ServiceModel.InstanceContext(this);
            _client = new ServiceLive.ServiceLiveClient(context);

            try
            {
                _client.SubscribeAsync();
            }
            catch (Exception)
            {
                MessageBox.Show("Erreur lors de la récupération des données Live, veuillez réessayer.", "Erreur");
            }
        }

        /// <summary>
        /// Stop live service data push
        /// </summary>
        private void StopServiceLiveExecute()
        {
            if (_client != null)
            {
                _client.Abort();
                _client.Close();
            }
        }

        /// <summary>
        /// Handle heart data from duplex web service
        /// </summary>
        /// <param name="requestData"></param>
        public void PushDataHeart(double requestData)
        {
            try
            {
                if (Hearts.Count >= 30)
                    Hearts.RemoveAt(0);

                Hearts.Add(new ChartObject() { Category = DateTime.Now.ToString(), NumberDouble = requestData });
            }
            catch (Exception)
            {
            }
        }

        /// <summary>
        /// Handle temperature data from duplex web service
        /// </summary>
        /// <param name="requestData"></param>
        public void PushDataTemp(double requestData)
        {
            try
            {
                if (Temperatures.Count >= 10)
                    Temperatures.RemoveAt(0);

                Temperatures.Add(new ChartObject() { Category = DateTime.Now.ToString(), NumberDouble = requestData });
            }
            catch (Exception)
            {
            }
        }

        #endregion Methods
    }
}