using parent_bMedecine.DataAccess.Patient;
using System.Collections.Generic;

namespace parent_bMedecine.BusinessManagement.Patient
{
    /// <summary>
    /// PatientDataService class
    /// </summary>
    public class PatientDataService : IPatientDataService
    {
        /// <summary>
        /// DataAccess object
        /// </summary>
        private readonly IPatientDataAccess _patientDataAccess;

        /// <summary>
        /// Constructor
        /// </summary>
        /// <param name="patientDataAccess">injected by SimpleIoC, see ViewModelLocator</param>
        public PatientDataService(IPatientDataAccess patientDataAccess)
        {
            _patientDataAccess = patientDataAccess;
        }

        public List<ServicePatient.Patient> GetListPatient()
        {
            return _patientDataAccess.GetListPatient();
        }

        public ServicePatient.Patient GetPatient(int id)
        {
            return _patientDataAccess.GetPatient(id);
        }

        public bool AddPatient(ServicePatient.Patient patient)
        {
            return _patientDataAccess.AddPatient(patient);
        }

        public bool DeletePatient(int id)
        {
            return _patientDataAccess.DeletePatient(id);
        }
    }
}