namespace parent_bMedecine.BusinessManagement.Observation
{
    /// <summary>
    /// IObservationDataService interface
    /// </summary>
    public interface IObservationDataService
    {
        /// <summary>
        /// Add observation for a given patient
        /// </summary>
        /// <param name="idPatient">the patient's id</param>
        /// <param name="obs">the observation to be added</param>
        /// <returns>true if added, false otherwise</returns>
        bool AddObservation(int idPatient, ServiceObservation.Observation obs);
    }
}