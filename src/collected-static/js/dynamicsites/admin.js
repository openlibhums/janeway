django.dynamicsites = {
    domainToFolderName: function() {
        var domain = django.jQuery('#id_domain').val();
        if (domain) {
            return this.folderNameCheck = domain.toLowerCase().replace(/[\s\-.]/g,'_').replace(/[^a-z0-9_]/g,'');
        }
        return '';
    },
    folderNameCheck: '',
}

django.jQuery(document).ready(function() {
    django.dynamicsites.folderNameCheck = django.jQuery('#id_folder_name').val();
    if (!django.dynamicsites.folderNameCheck) {
        // 1. if there's nothing in folderName, attach event listener to 
        //    domain to update folderName dynamically, until the user may edit 
        //    folderName
        django.jQuery('#id_domain').change(function() {
            var folder_name = django.jQuery('#id_folder_name').val();
            if(folder_name == django.dynamicsites.folderNameCheck) {
                django.jQuery('#id_folder_name').val(django.dynamicsites.domainToFolderName());
            }
        });
        // 2. if there's nothing in folderName and something in domain, 
        //    autopopulate folderName
        django.jQuery('#id_folder_name').val(django.dynamicsites.domainToFolderName());
    }
});
