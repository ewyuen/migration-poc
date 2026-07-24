using System;
using System.Collections.Generic;
using System.Diagnostics;

namespace parent_bMedecine.DataAccess.Patient
{
    /// <summary>
    /// PatientDataAccess class
    /// </summary>
    public class PatientDataAccess : IPatientDataAccess
    {
        public List<ServicePatient.Patient> GetListPatient()
        {
            ServicePatient.ServicePatientClient client = new ServicePatient.ServicePatientClient();
            List<ServicePatient.Patient> res;

            try
            {
                res = client.GetListPatient();
                client.Close();
            }
            catch (Exception ex)
            {
                Debug.WriteLine("PatientDataAccess: GetListPatient: Exception:" + ex.Message);
                res = null;
            }

            return res;
        }

        public ServicePatient.Patient GetPatient(int id)
        {
            ServicePatient.ServicePatientClient client = new ServicePatient.ServicePatientClient();
            ServicePatient.Patient res;

            try
            {
                res = client.GetPatient(id);
                client.Close();
            }
            catch (Exception ex)
            {
                Debug.WriteLine("PatientDataAccess: GetPatient: Exception:" + ex.Message);
                res = null;
            }

            return res;
        }

        public bool AddPatient(ServicePatient.Patient patient)
        {
            ServicePatient.ServicePatientClient client = new ServicePatient.ServicePatientClient();
            bool res;

            try
            {
                res = client.AddPatient(patient);
                client.Close();
            }
            catch (Exception ex)
            {
                Debug.WriteLine("PatientDataAccess: AddPatient: Exception:" + ex.Message);
                res = false;
            }

            return res;
        }

        public bool DeletePatient(int id)
        {
            ServicePatient.ServicePatientClient client = new ServicePatient.ServicePatientClient();
            bool res;

            try
            {
                res = client.DeletePatient(id);
                client.Close();
            }
            catch (Exception ex)
            {
                Debug.WriteLine("PatientDataAccess: DeletePatient: Exception:" + ex.Message);
                res = false;
            }

            return res;
        }
    }
}