using System;
using System.Diagnostics;

namespace parent_bMedecine.DataAccess.Observation
{
    /// <summary>
    /// ObservationDataAccess class
    /// </summary>
    public class ObservationDataAccess : IObservationDataAccess
    {
        public bool AddObservation(int idPatient, ServiceObservation.Observation obs)
        {
            ServiceObservation.ServiceObservationClient client = new ServiceObservation.ServiceObservationClient();
            bool res;

            try
            {
                res = client.AddObservation(idPatient, obs);
                client.Close();
            }
            catch (Exception ex)
            {
                Debug.WriteLine("PatientDataAccess: GetPatient: Exception:" + ex.Message);
                res = false;
            }

            return res;
        }
    }
}