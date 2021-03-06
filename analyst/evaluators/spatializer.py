from abc import abstractmethod

from ..clustertypes.cluster import Cluster
from .evaluator import Evaluator


"""
        .          .     .
      .  ..  .        .            .
     .. :...   .         .            ..            .
      . .::  :    ..  ..    :   .
    .    ..   .      .:: ..     .
        .    .     . .: .                 
                :      .   .               .
      ..            .       .
            . :                     =-o                  *
           . . : .        .             .
     .       .           .  .
          .           .        "Space, the Final Frontier..."
"""


class Spatializer(Evaluator, object):
    """
    What: An class for general spatial analysis, to analyze the embedding space
        properties as a whole.
    Why: It seems to me that unless we better understand some quantitative
        properties of the embedding spaces we work with, it will be hard to
        know what to do to improve them, or why improvements we make work.
    How: You can override this if you want, to have custom stats, but otherwise
        just use it as a built-in. Instead of having to make a Spatializer
        instance, you can just put "Spatial" or "All" in as a string, and the
        Analyst will do it for you, as with all built-in evaluators.
    """

    def __init__(self, category="Spatial", node_category="Nodes", starred=None,
            neighbors_to_stat=None):
        super(Spatializer, self).__init__(category=category, starred=starred)
        #   To inherit, must call parent init.
        self.node_category = node_category
        self.neighbors_to_stat = neighbors_to_stat
        #   Can override the automatic behavior to stat all neighbors computed.

        # PARENT MEMBERS WE NEED:
        # self.CATEGORY
        # self.data_dict
        # self.starred
        # self.calculated


    # OVERRIDEABLE
    def compute_stats(self, **kwargs):
        # kwargs: see Evaluator class.
        # POST: self.data_dict, self.starred filled in.
        encoder           = kwargs["encoder_fn"]
        metric            = kwargs["metric_fn"]
        metric_str        = kwargs["metric_str"]
        nearest           = kwargs["generic_nearest_fn"]
        printer           = kwargs["printer_fn"]
        find_evaluator    = kwargs["find_evaluator_fn"]
        metric_args       = kwargs["metric_args"]
        objects           = kwargs["strings"]
        space             = kwargs["embeddings"]
        neighbors_dist    = kwargs["kth_neighbors_dist_fn"]
        neighbors_to_stat = kwargs["make_kth_neighbors"] \
            if self.neighbors_to_stat is None else self.neighbors_to_stat

        self.data_dict["Distance Metric"] = metric_str

        # It is acceptable and useful to make one clusterizer depend on
        #   results from another. It is a BAD idea to try to make two
        #   depend on each other!
        self.node_clusterizer = find_evaluator(
            self.node_category, force_creation=False)

        # Allowing that find_evaluator may return None, in case user
        #   doesn't want Nodes calculated.
        nodes = []
        if self.node_clusterizer == None:
            printer("WARNING: " + self.node_category + " category not \
                found! " + self.CATEGORY + " will have no information on \
                contained Nodes")
        else:
            nodes = self.node_clusterizer.get_clusters(**kwargs)
        
        # Use the Cluster class to compute the main stats for us:
        printer("Balancing the Continuum", "Computing Common Spatial Stats")
        cluster = Cluster(self.CATEGORY, encoder, metric, objects,
            nearest=nearest, vectors=space, nodes=nodes, auto=True,
            **metric_args)

        if len(space) > 0:
            # Overall Info:
            self.data_dict["Dimensionality"] = len(space[0])
            self.data_dict["Population"] = cluster.stats_dict["Population"]
            printer("Electing a Ruler", "Getting Medoid, Etc.")
            self.data_dict["Medoid - Obj Nearest to Centroid"] = cluster.medoid
            
            skip = cluster.QUIET_STATS if cluster.quiet_stats_override is None \
                else cluster.quiet_stats_override
            for key in cluster.stats_dict:
                if key not in skip:
                    self.data_dict[key] = cluster.stats_dict[key]

            # Centroid Info:
            printer("Setting Priorities", "Centroid Stats")
            self._compute_list_stats(cluster.centroid_distances,
                "Centroid Dist", self.data_dict)
            self._compute_list_stats(cluster.norms, "Norms", self.data_dict)
            
            # Then re-key one entry:
            dispersion = self.data_dict.pop("Centroid Dist Avg")
            self.data_dict["Dispersion - Centroid Dist Avg"] = dispersion

            # kth-Neighbors Distance Info:
            for n in neighbors_to_stat:
                if n == 1:  # Added here because this is an OrderedDict
                    printer("Building Trade Routes", "Nearest Neighbor Stats")
                    printer("Practicing Diplomacy")
                    self.data_dict["Repulsion - Nearest Dist Avg"] = 0
                if n == 2:  # For fun
                    printer("Coming up with Excuses", "Second Neighbor Stats")
                if n == -1: # Added here because this is an OrderedDict
                    printer("Making Enemies", "Furthest Neighbor Stats")
                    self.data_dict["Broadness - Furthest Dist Max"] = 0
                self._compute_list_stats(neighbors_dist(n),
                    "Nghbr " + str(n) + " Dist", self.data_dict)

            # Some Re-keying for Specificity:
            repulsion = self.data_dict.pop("Nghbr 1 Dist Avg", None)
            broadness = self.data_dict.pop("Nghbr -1 Dist Max", None)
            printer("Claiming Frontiers", "Re-Keying Stuff")
            if repulsion is not None:
                self.data_dict["Repulsion - Nearest Dist Avg"] = repulsion
            if broadness is not None:
                self.data_dict["Broadness - Furthest Dist Max"] = broadness

            # Add stars to things we think are important or more interesting:
            printer("Counting the Lightyears", "Adding Stars")
            self.add_star("Medoid - Obj Nearest to Centroid")
            self.add_star("Dispersion - Centroid Dist Avg")
            self.add_star("Repulsion - Nearest Dist Avg")
            self.add_star("Nearest Dist Range")
            self.add_star("Broadness - Furthest Dist Max")