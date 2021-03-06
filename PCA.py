#!/usr/bin/env python

# This script checks all .pdb files in a directory, and writes to a text file
# the coordinates of the C-alphas of all those .pdb files
# It also extracts information stored in the REMARK statement at the top of
# each .pdb.
# A sub-list of residues can be submitted (for example binding pocket residues)
# so that the coordinates of only those residues are extracted and saved.
#
# https://github.com/thomas-coudrat/toolbx_pdb
# Thomas Coudrat <thomas.coudrat@gmail.com>

import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d import proj3d
import sys


class Principal_component_analysis:

    def __init__(self, conformations):
        """
        Create the PCA instance
        """
        self.conformations = conformations
        self.pcaCoordsArray = None
        self.vars_data = None

    def makePCAcoords(self, consensusResidues):
        """
        Create the PCA data on self.conformations
        """
        # This will store the coordinates of all conformations in a list
        allConfCoords = []

        # Go through the conformations in alphanumeric order
        sortedConfNames = sorted(self.conformations.keys())
        # sortedConfNames.sort()

        for confName in sortedConfNames:
            # Get the dictionary, and the file path
            conformationDict = self.conformations[confName]
            confPath = conformationDict['path']

            # Get the consensus residue list (if consensusResidues is True)
            if consensusResidues:
                resList = conformationDict['complex'].getResiduesConsensus()
            # Otherwise get the wole residue sequence
            else:
                resList = conformationDict['complex'].getResidues()
            # Generate the list of residues and format numbering to match that
            # of the .pdb files to which it gets compared
            resNumbers = [x.split("_")[0].lstrip("0") for x in resList]

            # Get the coords from that .pdb file
            confCoords = self.getPDBcoord(confPath, resNumbers)

            # Add this conformation's coordinates to the master array
            allConfCoords.append(confCoords)

        # Create an array with this data, and store it in the variable
        # self.pcaCoordsArray
        self.pcaCoordsArray = np.array(allConfCoords)

        # Check that each element in the array (protein conformation) is of
        # then same length (contains the same features ie alpha carbon
        # coordinates)
        if not all([len(x) == len(self.pcaCoordsArray[0])
                    for x in self.pcaCoordsArray]):
            print("\nNumber of coordinates not identical" +
                  " amongst conformations")
            for confName, coords in zip(sortedConfNames, self.pcaCoordsArray):
                print(confName, "\t", len(coords))
            print("Exiting.")
            sys.exit()

        # Verify that coordinates files are not empty
        if all([x.size == 0 for x in self.pcaCoordsArray]):
            print("No coordinates were passed to the PCA plotting " +
                  "function. Exiting.")
            sys.exit()

    def getPDBcoord(self, pdbPath, resNumbers):
        """
        Get a pdbPath, read that .pdb, and store the C-alpha data for that
        conformation
        Return an array for this conformation of the C-alpha x y z coordinates
        """
        pdbFile = open(pdbPath, "r")
        pdbLines = pdbFile.readlines()
        pdbFile.close()

        # This stores the conformations for .pdb file
        confCoords = []
        for line in pdbLines:
            ll = line.split()
            colCount = len(ll)
            if colCount > 1:
                # Check only lines that contain the ATOM description line
                if ll[0] == 'ATOM':
                    # If element at position 4 is alphabet, then the pdb files
                    # has a chain name, find the residue column in position 5.
                    # Otherwise, if position 4 is digit, that is the residue
                    # column (no chain name in that pdb)
                    if ll[4].isalpha():
                        resCol = 5
                    elif ll[4].isdigit():
                        resCol = 4
                    else:
                        print("Unrecognized pdb format, check number of " +
                              "columns. Exiting.")
                        sys.exit()
                    # Check that the current residue is within the list of
                    # consensus residues. Only get all the C-alphas
                    if ll[resCol] in resNumbers and ll[2] == 'CA':
                        xCoord = float(line[31:39].strip())
                        yCoord = float(line[39:47].strip())
                        zCoord = float(line[47:55].strip())
                        confCoords = np.concatenate([confCoords, [xCoord]])
                        confCoords = np.concatenate([confCoords, [yCoord]])
                        confCoords = np.concatenate([confCoords, [zCoord]])

        return confCoords

    def makePCAmetric(self, metric):
        """
        Create a self.vars_data list of variables data, to be used for the
        plotting of PCA graphs.
        """
        # Initialize the self.allVariables dict, based on the variable string
        # list passed as argument
        self.vars_data = {}
        self.vars_data[metric] = []

        # Go through the conformations in alphanumeric order
        sortedConfNames = sorted(self.conformations.keys())
        # sortedConfNames.sort()

        for confName in sortedConfNames:
            # Get the dictionary, and the file path
            conformationDict = self.conformations[confName]

            # Go over the sorted variable data, and for each variable dataset,
            # add the value of the current conformation
            sorted_var_names = sorted(self.vars_data.keys())
            for varName in sorted_var_names:
                confVar = conformationDict[varName]
                self.vars_data[varName].append(confVar)

    def plotPCAfig(self, projName, metric, labels, dim, templates):
        """
        After the coords onto which apply PCA have been extracted and stored
        in self.pcaCoordsArray, and..
        After the variables data have been extracted and stored in
        self.vars_all_data
        This function can be called to calculate the PCA of dimension 2 or 3,
        and call the plotting function to add subplots for each variable to
        be displayed
        """
        if self.pcaCoordsArray is not None:

            # Calculate PCA
            dpiVal = 800
            pca = PCA(n_components=dim)
            X_r = pca.fit(self.pcaCoordsArray).transform(self.pcaCoordsArray)
            # print X_r

            # Percentage of variance explained for each components
            print('Explained variance ratio (first ' + str(dim) +
                  ' components): %s' % str(pca.explained_variance_ratio_))
            # Round PC values for plotting
            round_val = 2
            PCs_round = [round(100 * pc, round_val)
                         for pc in pca.explained_variance_ratio_]
            print("PCs rounded at {} decimals: ".format(round_val), PCs_round)

            # print X_r[:, 0]
            # print X_r[:, 1]
            # print X_r[:, 2]

            # Get the variable/metric to plot. Store the information in
            # var_axis and var_data. Store None if no variable should be
            # plotted
            if self.vars_data is not None:
                if metric in self.vars_data.keys():
                    # Get the variable data
                    var_data = self.vars_data[metric]
                    if metric == "tanimoto":
                        var_axis = "Tanimoto coefficient"
                    elif metric == "jaccard":
                        var_axis = "Jaccard distance"
                    else:
                        var_axis = metric
                else:
                    print("The variable {} is not in " +
                          "the loaded set".format(metric))
            else:
                var_data = None
                var_axis = None

            # Plot the PCA scores, either 2D or 3D
            if dim == 2:
                if var_data:
                    self.pcaSubplot_vars(X_r, dim, var_data, var_axis,
                                         PCs_round, labels, templates, dpiVal)
                else:
                    self.pcaSubplot(X_r, dim, PCs_round, labels, templates,
                                    dpiVal)

                # Save the figure in svg format (and png for quick
                # visualization)
                plt.savefig(projName + "_PCA.svg", bbox_inches="tight")
                plt.savefig(projName + "_PCA.png", bbox_inches="tight",
                            dpi=dpiVal)
            if dim == 3:
                if var_data:
                    self.pcaSubplot_vars(X_r, dim, var_data, var_axis,
                                         PCs_round, labels, templates, dpiVal)
                else:
                    self.pcaSubplot(X_r, dim, PCs_round, labels, templates,
                                    dpiVal)

                # Save the figure in svg format (and png for quick
                # visualization)
                plt.savefig(projName + "_PCA3D.svg", bbox_inches="tight")
                plt.savefig(projName + "_PCA3D.png", bbox_inches="tight",
                            dpi=dpiVal)

        else:
            print("The coords onto which apply the PCA have to be extracted")
            print("First run initPCA() then generateProtCoords()")

    def pcaSubplot_vars(self, X_r, dim, varData, varName, PCs_round, labels,
                        template_list, dpiVal):
        """
        Get the Principal Component Analysis data for this set of coordinates
        The value of 'dim' specifies the number of dimensions to diplay
        Then plot the PCA data
        """
        # Set some figure parameters
        plt.rcParams['xtick.major.pad'] = '8'
        plt.rcParams['ytick.major.pad'] = '8'

        # Divide up the data to plot into general conformations and templates.
        # The colormap data is not used for the templates, and a different
        # marker is used.
        templatePosition = []
        confData = []
        confPosition = []
        for l, d, x in zip(labels, varData, X_r):
            if l in template_list:
                templatePosition.append(x)
            else:
                confData.append(d)
                confPosition.append(x)
        templatePosition = np.array(templatePosition)
        confPosition = np.array(confPosition)

        # Plot either PCA data on 2D or 3D
        if dim == 2:
            # Create figure and subplot
            fig = plt.figure(figsize=(17, 13), dpi=dpiVal)
            fig.set_facecolor('white')
            fig.canvas.set_window_title("PCA 2D")
            ax = fig.add_subplot(111)

            # Scatter conformations. Designated by circles, colored based on
            # IFP similarity to a defined template
            scat = ax.scatter(confPosition[:, 0], confPosition[:, 1],
                              s=600, marker="o",
                              cmap=plt.cm.magma,
                              c=confData,
                              vmin=0.0, vmax=1.0)

            # Scatter the template conformation(s). Designated by arrows.
            ax.scatter(templatePosition[:, 0], templatePosition[:, 1],
                       s=600, marker="v", color="black")

            # Setting labels for both conformations and templates
            for label, x, y in zip(labels, X_r[:, 0], X_r[:, 1]):
                ax.annotate(label, xy=(x, y + 0.05), fontsize=30,
                            ha='center', va='bottom')

            # Settin axis and labels
            ax.set_xlabel("PC1 ({} %)".format(PCs_round[0]), fontsize=30)
            ax.set_ylabel("PC2 ({} %)".format(PCs_round[1]), fontsize=30)
            ax.tick_params(axis="both", which="major", labelsize=25)

            # Plot the colorbar
            cb = plt.colorbar(scat)
            cb.set_label(varName, size=30)
            cb.ax.tick_params(labelsize=25)

        # 3D figure
        if dim == 3:
            # Create figure and subplot
            fig = plt.figure()
            fig.set_facecolor('white')
            fig.canvas.set_window_title("PCA 3D")
            ax = fig.add_subplot(111, projection='3d')

            # Conformations
            scat = ax.scatter(confPosition[:, 0],
                              confPosition[:, 1],
                              confPosition[:, 2],
                              s=200, marker="o",
                              cmap=plt.cm.magma,
                              c=confData,
                              vmin=0.0, vmax=1.0)
            # Templates
            ax.scatter(templatePosition[:, 0],
                       templatePosition[:, 1],
                       templatePosition[:, 2],
                       c="black", s=200, marker="v")

            # Scatter plot labels
            for label, x, y, z in zip(labels, X_r[:, 0], X_r[:, 1], X_r[:, 2]):
                if label != "":
                    x2D, y2D, _ = proj3d.proj_transform(x, y, z, ax.get_proj())
                    ax.annotate(label, xy=(x2D, y2D), fontsize=10,
                                ha='left', va='top')

            # Setting axis and labelsize
            ax.set_xlabel("PC1 ({} %)".format(PCs_round[0]), fontsize=10)
            ax.set_ylabel("PC2 ({} %)".format(PCs_round[1]), fontsize=10)
            ax.set_zlabel("PC3 ({} %)".format(PCs_round[2]), fontsize=10)
            ax.tick_params(axis="both", which="major", labelsize=10)

            # Plot the colorbar
            cb = plt.colorbar(scat)
            cb.set_label(varName, size=10)
            cb.ax.tick_params(labelsize=10)

    def pcaSubplot(self, X_r, dim, PCs_round, labels, template_list, dpiVal):
        """
        Get the Principal Component Analysis data for this set of coordinates
        The value of 'dim' specifies the number of dimensions to diplay
        Then plot the PCA data
        """
        # Set some figure parameters
        plt.rcParams['xtick.major.pad'] = '8'
        plt.rcParams['ytick.major.pad'] = '8'

        # Plot either PCA data on 2D or 3D
        if dim == 2:
            fig = plt.figure(figsize=(15, 13), dpi=dpiVal)
            fig.set_facecolor('white')
            fig.canvas.set_window_title("PCA 2D")
            ax = fig.add_subplot(111)

            # Scatter conformations. Designated by circles, colored based on
            # IFP similarity to a defined template
            scat = ax.scatter(X_r[:, 0], X_r[:, 1],
                              s=600, marker="v", color="black")

            # Setting labels for both conformations and templates
            for label, x, y in zip(labels, X_r[:, 0], X_r[:, 1]):
                ax.annotate(label, xy=(x, y + 0.06), fontsize=30,
                            ha='center', va='bottom')

        if dim == 3:
            fig = plt.figure()
            fig.set_facecolor('white')
            fig.canvas.set_window_title("PCA 3D")
            ax = fig.add_subplot(111, projection='3d')

            # Conformations
            scat = Axes3D.scatter(ax, X_r[:, 0], X_r[:, 1], X_r[:, 2],
                                  size=600, marker="o")

            # Scatter plot labels
            for label, x, y, z in zip(labels, X_r[:, 0], X_r[:, 1], X_r[:, 2]):
                if label != "":
                    x2D, y2D, _ = proj3d.proj_transform(x, y, z, ax.get_proj())
                    ax.annotate(label, xy=(x2D, y2D), fontsize=30,
                                ha='left', va='bottom')

        # Setting axes and labels
        ax.set_xlabel("PC1 ({} %)".format(PCs_round[0]))
        ax.xaxis.label.set_size(25)
        ax.set_ylabel("PC2 ({} %)".format(PCs_round[1]))
        ax.yaxis.label.set_size(25)
        if dim == 3:
            ax.set_zlabel("PC3 ({0} %)".format(PCs_round[2]))
            ax.zaxis.label.set_size(25)
        ax.tick_params(axis="both", which="major", labelsize=25)
