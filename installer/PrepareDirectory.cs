using System;
using System.IO;
using System.Security.AccessControl;
using System.Security.Principal;

// This folder contains a driver and programs that Windows runs as administrator.
internal static class PrepareDirectory
{
    private static readonly SecurityIdentifier Admins = Sid(WellKnownSidType.BuiltinAdministratorsSid);
    private static readonly SecurityIdentifier SystemAccount = Sid(WellKnownSidType.LocalSystemSid);
    private static readonly SecurityIdentifier Users = Sid(WellKnownSidType.BuiltinUsersSid);

    private static SecurityIdentifier Sid(WellKnownSidType type)
    {
        return new SecurityIdentifier(type, null);
    }

    private static DirectorySecurity InstallPermissions()
    {
        var acl = new DirectorySecurity();
        acl.SetOwner(Admins);
        acl.SetAccessRuleProtection(true, false);
        foreach (var sid in new[] { Admins, SystemAccount, Users })
        {
            var rights = sid == Users ? FileSystemRights.ReadAndExecute : FileSystemRights.FullControl;
            acl.AddAccessRule(new FileSystemAccessRule(sid, rights,
                InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit,
                PropagationFlags.None, AccessControlType.Allow));
        }
        return acl;
    }

    private static bool Protected(FileSystemSecurity acl)
    {
        var owner = acl.GetOwner(typeof(SecurityIdentifier));
        if (!owner.Equals(Admins) && !owner.Equals(SystemAccount)) return false;
        const FileSystemRights writes = FileSystemRights.Write | FileSystemRights.Delete |
            FileSystemRights.DeleteSubdirectoriesAndFiles | FileSystemRights.ChangePermissions |
            FileSystemRights.TakeOwnership;
        foreach (FileSystemAccessRule rule in acl.GetAccessRules(true, true, typeof(SecurityIdentifier)))
        {
            if (rule.AccessControlType == AccessControlType.Allow && (rule.FileSystemRights & writes) != 0 &&
                !rule.IdentityReference.Equals(Admins) && !rule.IdentityReference.Equals(SystemAccount)) return false;
        }
        return true;
    }

    private static bool CheckTree(FileSystemInfo item)
    {
        if ((item.Attributes & FileAttributes.ReparsePoint) != 0) return false;
        var dir = item as DirectoryInfo;
        if (dir == null) return Protected(((FileInfo)item).GetAccessControl());
        if (!Protected(dir.GetAccessControl())) return false;
        foreach (var child in dir.EnumerateFileSystemInfos())
            if (!CheckTree(child)) return false;
        return true;
    }

    public static int Main(string[] args)
    {
        try
        {
            if (args.Length != 1) return 1;
            var dir = new DirectoryInfo(args[0]);
            if (!dir.Name.Equals("ZapretApp-discord-youtube-telegram", StringComparison.OrdinalIgnoreCase))
                return 1;
            for (var parent = dir; parent != null; parent = parent.Parent)
                if (parent.Exists && (parent.Attributes & FileAttributes.ReparsePoint) != 0) return 1;
            dir.Create(InstallPermissions());
            if (!Protected(dir.GetAccessControl()))
            {
                // Earlier versions used this folder only for downloaded archives.
                foreach (var entry in dir.EnumerateFileSystemInfos())
                    if (!IsLegacyCache(entry)) return 1;
                dir.SetAccessControl(InstallPermissions());
            }
            if (!Protected(dir.GetAccessControl())) return 1;
            foreach (var entry in dir.EnumerateFileSystemInfos())
                if (!IsLegacyCache(entry) && !CheckTree(entry)) return 1;
            return 0;
        }
        catch (Exception e)
        {
            Console.Error.WriteLine(e.Message);
            return 1;
        }
    }

    private static bool IsLegacyCache(FileSystemInfo entry)
    {
        return entry is DirectoryInfo && (entry.Attributes & FileAttributes.ReparsePoint) == 0 &&
            (entry.Name.Equals("zapret", StringComparison.OrdinalIgnoreCase) ||
             entry.Name.Equals("telegram", StringComparison.OrdinalIgnoreCase));
    }
}
