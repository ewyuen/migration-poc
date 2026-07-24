using parent_bMedecine.DataAccess.Observation;

namespace parent_bMedecine.BusinessManagement.Observation
{
    /// <summary>
    /// ObservationDataService class
    /// </summary>
    public class ObservationDataService : IObservationDataService
    {
        /// <summary>
        /// DataAccess object
        /// </summary>
        private readonly IObservationDataAccess _observationDataAccess;

        /// <summary>
        /// Constructor
        /// </summary>
        /// <param name="observationDataAccess">injected by SimpleIoC, see ViewModelLocator</param>
        public ObservationDataService(IObservationDataAccess observationDataAccess)
        {
            _observationDataAccess = observationDataAccess;
        }

        public bool AddObservation(int idPatient, ServiceObservation.Observation obs)
        {
            return _observationDataAccess.AddObservation(idPatient, obs);
        }
    }
}