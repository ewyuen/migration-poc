using GalaSoft.MvvmLight.Messaging;

namespace parent_bMedecine.Message
{
    /// <summary>
    /// Message sent to ViewModels when the user selects a patient
    /// </summary>
    public class OnPatientSelectionMessage : MessageBase
    {
        /// <summary>
        /// Patient selected by the user
        /// </summary>
        public ServicePatient.Patient SelectedPatient { get; set; }

        /// <summary>
        /// Constructor
        /// </summary>
        /// <param name="selectedPatient">patient selected by the user</param>
        public OnPatientSelectionMessage(ServicePatient.Patient selectedPatient)
        {
            SelectedPatient = selectedPatient;
        }
    }
}