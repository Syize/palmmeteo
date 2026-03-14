"""
workflow.py - Workflow management

This module contains classes for managing and indexing workflow stages.
"""

from typing import List, Any
from ..exceptions import WorkflowError

class Workflow:
    """
    Indexes and maintains the workflow as a sequence of named stages.
    
    This class manages the workflow stages, including assigning, validating,
    and iterating over the stages.
    """

    def __init__(self, default_stages: List[str]):
        """
        Initialize a Workflow instance.
        
        Parameters
        ----------
        default_stages : List[str]
            List of all available workflow stages in order
        """
        self.default_stages = default_stages
        self.idx = {s:i for i, s in enumerate(default_stages)}
        self.snapshot_from = None

    def stage_idx(self, s: str) -> int:
        """
        Get the index of a stage by name.
        
        Parameters
        ----------
        s : str
            Name of the stage
        
        Returns
        -------
        int
            Index of the stage
        
        Raises
        ------
        WorkflowError
            If the stage name is unknown
        """
        try:
            return self.idx[s]
        except KeyError:
            raise WorkflowError(f'Unknown workflow stage: "{s}". Valid workflow stages are: {self.default_stages}.')

    def assign_all(self) -> None:
        """Assign all available stages to the workflow."""
        self.workflow = self.default_stages

    def assign_fromto(self, stage_from: str, stage_to: str) -> None:
        """
        Assign a range of stages to the workflow.
        
        Parameters
        ----------
        stage_from : str or None
            Start stage (None for beginning)
        stage_to : str or None
            End stage (None for end)
        
        Raises
        ------
        WorkflowError
            If a stage name is unknown
        """
        try:
            wf1 = self.stage_idx(stage_from) if stage_from else 0
            wf2 = self.stage_idx(stage_to)   if stage_to   else -1
        except KeyError as e:
            raise WorkflowError(f'Unknown stage: {e.args[0]}')

        self.workflow = self.default_stages[wf1:wf2+1]
        if wf1 > 0:
            self.snapshot_from = self.default_stages[wf1-1]

    def assign_list(self, stages: List[str]) -> None:
        try:
            workflow = [self.stage_idx(s) for s in stages]
        except KeyError as e:
            raise WorkflowError(f'Unknown stage: {e.args[0]}')

        gaps = [i for i in range(1, len(workflow))
                if workflow[i-1]+1 != workflow[i]]
        if len(gaps) == 1:
            before = workflow[:gaps[0]]
            after = workflow[gaps[0]]
            if before in ([0], [0,1]) and after >= 2:
                self.snapshot_from = self.default_stages[after-1]
                from ..logging import warn
                warn('Partially supported non-continuous workflow. Snapshot '
                     'will be loaded from stage {}. Success is not '
                     'guaranteed.', self.snapshot_from)
                gaps = None
        else:
            if workflow[0] > 0:
                self.snapshot_from = self.default_stages[workflow[0]-1]

        if gaps:
            # Apart from supported case above
            raise WorkflowError(f'Unsupported non-contiguous workflow! Selected stages {stages}. Complete workflow: {self.default_stages}.')

        self.workflow = [self.default_stages[si] for si in workflow]

    def __iter__(self):
        return iter(self.workflow)
