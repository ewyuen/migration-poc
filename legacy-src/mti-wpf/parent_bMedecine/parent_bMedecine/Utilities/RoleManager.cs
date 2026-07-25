namespace parent_bMedecine.Utilities
{
    /// <summary>
    /// Class to handle roles
    /// </summary>
    public class RoleManager
    {
        /// <summary>
        /// Returns true if the role has only read rights
        /// </summary>
        /// <param name="role">the role as string</param>
        /// <returns>true if role is readonly</returns>
        public static bool IsReadOnlyRole(string role)
        {
            return role.ToLower().Equals("infirmiere") || role.ToLower().Equals("infirmière");
        }
    }
}