import unittest
from unittest.mock import patch, MagicMock
from visualizer import (
    get_git_commits,
    get_commit_diff,
    generate_mermaid_graph,
    generate_png_from_mermaid
)


class TestDependencyVisualizer(unittest.TestCase):

    @patch('subprocess.run')
    def test_get_git_commits(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout='abc123 def456\ndef456\n',
            returncode=0
        )
        expected = [('abc123', ['def456']), ('def456', [])]
        result = get_git_commits('/path/to/repo')
        self.assertEqual(result, expected)

    @patch('subprocess.run')
    def test_get_commit_diff(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout='src/main.py\nsrc/utils/helper.py\n',
            returncode=0
        )
        expected_folders = ['src', 'src/utils']
        expected_files = ['src/main.py', 'src/utils/helper.py']
        folders, files = get_commit_diff('/path/to/repo', 'abc123')
        self.assertCountEqual(folders, expected_folders)
        self.assertCountEqual(files, expected_files)

    def test_generate_mermaid_graph(self):
        commits = [
            ('abc123', ['def456']),
            ('def456', [])
        ]
        with patch('visualizer.get_commit_diff') as mock_diff:
            mock_diff.side_effect = [
                (['src'], ['src/main.py']),
                (['tests'], ['tests/test_main.py'])
            ]
            mermaid_graph = generate_mermaid_graph(commits, '/path/to/repo')
            self.assertIn('abc123', mermaid_graph)
            self.assertIn('def456', mermaid_graph)
            self.assertIn('def456 --> abc123', mermaid_graph)
            self.assertIn('src/main.py', mermaid_graph)
            self.assertIn('tests/test_main.py', mermaid_graph)

    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('os.remove')
    def test_generate_png_from_mermaid(self, mock_remove, mock_exists, mock_run):
        mock_exists.return_value = True
        mermaid_graph = 'graph TD\n A --> B'
        generate_png_from_mermaid(mermaid_graph, 'output.png', 'mmdc')
        mock_run.assert_called_once()
        mock_remove.assert_called_once_with('temp.mmd')


if __name__ == '__main__':
    unittest.main()
