class FileNameGenerator():

    def __init__(self):
        self.info = {}

    """
    Simple class that can be used to generate sequential file names for a given extension.
    """

    def getFileName(self, extension: str):
        """
        Generate a sequential filename for a given extension
        Parameters
        ----------
        extension the extension to be used in the generated filename

        Returns
        -------
        a filename in the following form:
            file_ddd.ext
        Where ddd will be a 3 digit number with leading zeros that's incremented each time the method is called for
        a particular extension. ext will be replace with given extension

        """
        if extension not in self.info.keys():
            self.info[extension] = 0
        file_name = f'file_{self.info[extension]:03d}.{extension}'
        self.info[extension] += 1
        return file_name
